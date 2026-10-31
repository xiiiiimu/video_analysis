package com.videodiagnosis.infrastructure.media;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.domain.valueobject.VideoMeta;
import com.videodiagnosis.infrastructure.storage.MinioStorageClient;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * ffmpeg / ffprobe / tesseract 的底层封装。
 *
 * <p>v0.2 起只提供"基于本地文件"的原子操作（probe、场景检测、按时间点抽帧、OCR、抽音轨），
 * 由 {@link VideoFeatureExtractor} 编排：一个视频只下载一次，再在本地文件上做所有处理。
 * 旧版每个步骤各自下载一次视频（同一个视频下载 4 次），并且只覆盖前 15 秒。
 */
@Component
public class FfmpegMediaAdapter {

    private static final Pattern PTS_TIME = Pattern.compile("pts_time:([0-9]+(?:\\.[0-9]+)?)");

    private final MinioStorageClient minioStorageClient;
    private final MediaProcessingProperties properties;
    private final ObjectMapper objectMapper;

    public FfmpegMediaAdapter(MinioStorageClient minioStorageClient,
                              MediaProcessingProperties properties,
                              ObjectMapper objectMapper) {
        this.minioStorageClient = minioStorageClient;
        this.properties = properties;
        this.objectMapper = objectMapper;
    }

    /** 上传登记时只需要元数据。 */
    public VideoMeta extractMeta(String fileUrl) {
        return withDownloadedVideo(fileUrl, videoPath -> probe(videoPath, fileUrl).meta());
    }

    /** 下载一次视频到临时目录，回调结束后清理。 */
    public <T> T withDownloadedVideo(String fileUrl, VideoFileCallback<T> callback) {
        Path workDir = null;
        try {
            workDir = Files.createTempDirectory("video-source-");
            Path videoPath = workDir.resolve("source-video");
            minioStorageClient.downloadTo(fileUrl, videoPath);
            return callback.execute(videoPath);
        } catch (IOException ex) {
            throw new IllegalStateException("Failed to prepare video file", ex);
        } finally {
            deleteRecursively(workDir);
        }
    }

    public ProbeResult probe(Path videoPath, String fileUrl) {
        CommandResult result = runCommand(List.of(
                properties.getFfprobePath(),
                "-v", "error",
                "-show_entries", "stream=codec_type,width,height:format=duration,bit_rate",
                "-of", "json",
                videoPath.toString()
        ), Map.of());
        try {
            JsonNode root = objectMapper.readTree(result.output());
            int width = 0;
            int height = 0;
            boolean hasAudio = false;
            for (JsonNode stream : root.path("streams")) {
                String type = stream.path("codec_type").asText("");
                if ("video".equals(type) && width == 0) {
                    width = stream.path("width").asInt(0);
                    height = stream.path("height").asInt(0);
                } else if ("audio".equals(type)) {
                    hasAudio = true;
                }
            }
            JsonNode format = root.path("format");
            long durationMs = Math.round(parseDouble(format.path("duration").asText("0")) * 1000);
            long bitrate = parseLong(format.path("bit_rate").asText("0"));
            String mimeType = fileUrl != null && fileUrl.toLowerCase(Locale.ROOT).endsWith(".mp4") ? "video/mp4" : "video/*";
            return new ProbeResult(new VideoMeta(durationMs, width, height, bitrate, mimeType), hasAudio);
        } catch (Exception ex) {
            throw new IllegalStateException("Failed to parse ffprobe output", ex);
        }
    }

    /**
     * 用 ffmpeg 的 scene 打分检测镜头切换，返回切换时间点（秒）。
     * 先缩到 320 宽再打分，速度快很多，对切换检测几乎没有影响。
     */
    public List<Double> detectSceneChanges(Path videoPath, double windowSeconds, double threshold) {
        CommandResult result = runCommand(List.of(
                properties.getFfmpegPath(),
                "-hide_banner",
                "-t", formatSeconds(windowSeconds),
                "-i", videoPath.toString(),
                "-an",
                "-vf", "scale=320:-2,select='gt(scene," + String.format(Locale.ROOT, "%.3f", threshold) + ")',showinfo",
                "-f", "null",
                "-"
        ), Map.of());
        List<Double> times = new ArrayList<>();
        Matcher matcher = PTS_TIME.matcher(result.output());
        while (matcher.find()) {
            double time = parseDouble(matcher.group(1));
            if (time > 0 && time < windowSeconds) {
                times.add(time);
            }
        }
        times.sort(Comparator.naturalOrder());
        return times;
    }

    /** 在指定时间点抽一帧；时间点超出视频末尾时返回 false。 */
    public boolean extractFrameAt(Path videoPath, double seconds, Path output) {
        runCommand(List.of(
                properties.getFfmpegPath(),
                "-hide_banner",
                "-y",
                "-ss", formatSeconds(seconds),
                "-i", videoPath.toString(),
                "-frames:v", "1",
                "-vf", "scale='min(" + Math.max(320, properties.getFrameWidth()) + ",iw)':-2",
                "-q:v", "3",
                output.toString()
        ), Map.of());
        try {
            return Files.exists(output) && Files.size(output) > 0;
        } catch (IOException ex) {
            return false;
        }
    }

    /** 对单张图片做 OCR，返回规整后的单行文本。 */
    public String ocrImage(Path imagePath) {
        if (!properties.isOcrEnabled()) {
            return "";
        }
        // 多个 tesseract 并行时限制每个进程只用 1 个线程，否则 OpenMP 会互相抢 CPU
        CommandResult result = runCommand(List.of(
                properties.getTesseractPath(),
                imagePath.toString(),
                "stdout",
                "-l", properties.getTesseractLanguages(),
                "--psm", "6"
        ), Map.of("OMP_THREAD_LIMIT", "1"));
        return normalizeOcrText(result.output());
    }

    /**
     * 抽取 [startSeconds, startSeconds + durationSeconds) 的音轨，单声道 16kHz mp3。
     * 2 分钟约 0.5MB，远低于转写接口 25MB 的上限。
     */
    public void extractAudio(Path videoPath, double startSeconds, double durationSeconds, Path output) {
        runCommand(List.of(
                properties.getFfmpegPath(),
                "-hide_banner",
                "-y",
                "-ss", formatSeconds(startSeconds),
                "-t", formatSeconds(durationSeconds),
                "-i", videoPath.toString(),
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-b:a", "32k",
                output.toString()
        ), Map.of());
    }

    static String normalizeOcrText(String text) {
        if (text == null) {
            return "";
        }
        return text.replace('\r', '\n')
                .lines()
                .map(String::trim)
                .filter(line -> !line.isBlank())
                .distinct()
                .reduce((left, right) -> left + " " + right)
                .orElse("");
    }

    /** 秒 -> HH:MM:SS（旧实现写死成 00:00:%02d，超过 60 秒会生成 00:00:63）。 */
    public static String formatTimestamp(double seconds) {
        long total = Math.max(0, (long) Math.floor(seconds));
        return String.format(Locale.ROOT, "%02d:%02d:%02d", total / 3600, (total % 3600) / 60, total % 60);
    }

    private static String formatSeconds(double seconds) {
        return String.format(Locale.ROOT, "%.3f", Math.max(0, seconds));
    }

    private CommandResult runCommand(List<String> command, Map<String, String> environment) {
        try {
            ProcessBuilder builder = new ProcessBuilder(command).redirectErrorStream(true);
            builder.environment().putAll(environment);
            Process process = builder.start();
            String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                String tail = output.length() > 2000 ? output.substring(output.length() - 2000) : output;
                throw new IllegalStateException("Media command failed (" + command.get(0) + "): " + tail);
            }
            return new CommandResult(output);
        } catch (IOException ex) {
            throw new IllegalStateException("Unable to start media command. Please install ffmpeg, ffprobe and tesseract.", ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Media command was interrupted", ex);
        }
    }

    public static void deleteRecursively(Path path) {
        if (path == null || !Files.exists(path)) {
            return;
        }
        try (var stream = Files.walk(path)) {
            stream.sorted(Comparator.reverseOrder()).forEach(item -> {
                try {
                    Files.deleteIfExists(item);
                } catch (IOException ignored) {
                    // Temporary media files are best-effort cleanup.
                }
            });
        } catch (IOException ignored) {
            // Temporary media files are best-effort cleanup.
        }
    }

    private static double parseDouble(String value) {
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException ex) {
            return 0;
        }
    }

    private static long parseLong(String value) {
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException ex) {
            return 0;
        }
    }

    public record ProbeResult(VideoMeta meta, boolean hasAudio) {
    }

    private record CommandResult(String output) {
    }

    @FunctionalInterface
    public interface VideoFileCallback<T> {
        T execute(Path videoPath) throws IOException;
    }
}
