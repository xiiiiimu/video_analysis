package com.videodiagnosis.infrastructure.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.infrastructure.media.FfmpegMediaAdapter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * 语音转写：ffmpeg 抽音轨 -> OpenAI 兼容的 /audio/transcriptions。
 *
 * <p>失败永远不抛异常：转写只是证据之一，不能因为网络 / Key 问题让整个预处理失败。
 * 结果里的 status 会如实告诉下游（agent）转写是否可用：ok / disabled / no_audio / failed。
 */
@Component
public class AsrClientAdapter {

    private static final Logger log = LoggerFactory.getLogger(AsrClientAdapter.class);
    private static final int MAX_ERROR_CHARS = 300;

    private final AsrProperties properties;
    private final FfmpegMediaAdapter ffmpegMediaAdapter;
    private final ObjectMapper objectMapper;
    private final RestClient restClient;

    public AsrClientAdapter(AsrProperties properties,
                            FfmpegMediaAdapter ffmpegMediaAdapter,
                            ObjectMapper objectMapper) {
        this.properties = properties;
        this.ffmpegMediaAdapter = ffmpegMediaAdapter;
        this.objectMapper = objectMapper;
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(properties.getConnectTimeoutMs());
        requestFactory.setReadTimeout(properties.getReadTimeoutMs());
        this.restClient = RestClient.builder()
                .baseUrl(trimTrailingSlash(properties.getBaseUrl()))
                .requestFactory(requestFactory)
                .build();
    }

    /**
     * @param videoPath     已下载到本地的视频
     * @param windowSeconds 只转写前 windowSeconds 秒（与抽帧分析窗口一致）
     * @param hasAudio      ffprobe 是否检测到音轨
     */
    public AsrResult transcribe(Path videoPath, double windowSeconds, boolean hasAudio) {
        if (!properties.isActive()) {
            return AsrResult.of(AsrResult.DISABLED, properties.getModel(), "ASR api key not configured");
        }
        if (!hasAudio) {
            return AsrResult.of(AsrResult.NO_AUDIO, properties.getModel(), "");
        }
        if (windowSeconds <= 0) {
            return AsrResult.of(AsrResult.NO_AUDIO, properties.getModel(), "empty window");
        }
        Path workDir = null;
        try {
            workDir = Files.createTempDirectory("video-asr-");
            List<AsrSegment> segments = properties.useSegmentMode()
                    ? transcribeWithSegments(videoPath, windowSeconds, workDir)
                    : transcribeChunked(videoPath, windowSeconds, workDir);
            return new AsrResult(AsrResult.OK, properties.getModel(), "", segments);
        } catch (Exception ex) {
            log.warn("ASR failed for {}: {}", videoPath, ex.getMessage());
            return AsrResult.of(AsrResult.FAILED, properties.getModel(), truncate(ex.getMessage()));
        } finally {
            FfmpegMediaAdapter.deleteRecursively(workDir);
        }
    }

    private List<AsrSegment> transcribeWithSegments(Path videoPath, double windowSeconds, Path workDir) throws IOException {
        Path audio = workDir.resolve("audio.mp3");
        ffmpegMediaAdapter.extractAudio(videoPath, 0, windowSeconds, audio);
        JsonNode root = post(audio, "verbose_json", true);
        List<AsrSegment> segments = new ArrayList<>();
        for (JsonNode segment : root.path("segments")) {
            String text = segment.path("text").asText("").trim();
            double start = segment.path("start").asDouble(0);
            double end = Math.min(segment.path("end").asDouble(start), windowSeconds);
            if (!text.isBlank() && start < windowSeconds) {
                segments.add(new AsrSegment(start, Math.max(start, end), text));
            }
        }
        if (segments.isEmpty()) {
            String text = root.path("text").asText("").trim();
            if (!text.isBlank()) {
                segments.add(new AsrSegment(0, windowSeconds, text));
            }
        }
        return segments;
    }

    private List<AsrSegment> transcribeChunked(Path videoPath, double windowSeconds, Path workDir) throws IOException {
        int chunk = Math.max(5, properties.getChunkSeconds());
        List<AsrSegment> segments = new ArrayList<>();
        int index = 0;
        for (double start = 0; start < windowSeconds - 0.5; start += chunk, index++) {
            double duration = Math.min(chunk, windowSeconds - start);
            Path audio = workDir.resolve(String.format("chunk-%03d.mp3", index));
            ffmpegMediaAdapter.extractAudio(videoPath, start, duration, audio);
            if (!Files.exists(audio) || Files.size(audio) == 0) {
                continue;
            }
            String text = post(audio, "json", false).path("text").asText("").trim();
            if (!text.isBlank()) {
                segments.add(new AsrSegment(start, start + duration, text));
            }
        }
        return segments;
    }

    private JsonNode post(Path audio, String responseFormat, boolean segmentTimestamps) throws IOException {
        MultiValueMap<String, Object> form = new LinkedMultiValueMap<>();
        form.add("file", new FileSystemResource(audio));
        form.add("model", properties.getModel());
        form.add("response_format", responseFormat);
        if (segmentTimestamps) {
            form.add("timestamp_granularities[]", "segment");
        }
        if (properties.getLanguage() != null && !properties.getLanguage().isBlank()) {
            form.add("language", properties.getLanguage().trim());
        }
        String body = restClient.post()
                .uri("/audio/transcriptions")
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + properties.getApiKey().trim())
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(form)
                .retrieve()
                .body(String.class);
        return objectMapper.readTree(body == null ? "{}" : body);
    }

    private static String trimTrailingSlash(String url) {
        if (url == null || url.isBlank()) {
            return "https://api.openai.com/v1";
        }
        return url.endsWith("/") ? url.substring(0, url.length() - 1) : url;
    }

    private static String truncate(String message) {
        if (message == null) {
            return "";
        }
        return message.length() > MAX_ERROR_CHARS ? message.substring(0, MAX_ERROR_CHARS) + "..." : message;
    }

    public record AsrSegment(double start, double end, String text) {
    }

    public record AsrResult(String status, String model, String error, List<AsrSegment> segments) {
        public static final String OK = "ok";
        public static final String DISABLED = "disabled";
        public static final String NO_AUDIO = "no_audio";
        public static final String FAILED = "failed";

        static AsrResult of(String status, String model, String error) {
            return new AsrResult(status, model, error, List.of());
        }

        public String fullText() {
            return segments.stream()
                    .map(AsrSegment::text)
                    .reduce((left, right) -> left + " " + right)
                    .orElse("");
        }
    }
}
