package com.videodiagnosis.infrastructure.media;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.valueobject.VideoMeta;
import com.videodiagnosis.infrastructure.client.AsrClientAdapter;
import com.videodiagnosis.infrastructure.storage.MinioStorageClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * 视频特征提取编排（v0.2，分析窗口默认 120 秒）。
 *
 * <p>一次下载 → probe → 场景检测 → 生成采样计划 → 并行抽帧 + OCR → 上传关键帧 → 转写音轨。
 * 产出写入 {@link VideoFeature}：
 * <ul>
 *   <li>keyframes：关键帧 URL 列表（按时间排序，兼容旧消费者）；</li>
 *   <li>sceneJson：真实的镜头切分（旧版是写死的 0~5 秒）；</li>
 *   <li>ocrJson：按时间合并后的屏幕文字，连续相同的字幕合成一段；</li>
 *   <li>transcriptText：转写全文；</li>
 *   <li>timelineJson：带时间戳的完整时间轴（关键帧 + 转写分段 + 截断信息），给 agent 用。</li>
 * </ul>
 */
@Component
public class VideoFeatureExtractor {

    public static final String FEATURE_VERSION = "0.2.0";
    private static final Logger log = LoggerFactory.getLogger(VideoFeatureExtractor.class);

    private final FfmpegMediaAdapter ffmpeg;
    private final AsrClientAdapter asrClient;
    private final MinioStorageClient minioStorageClient;
    private final MediaProcessingProperties properties;
    private final ObjectMapper objectMapper;

    public VideoFeatureExtractor(FfmpegMediaAdapter ffmpeg,
                                 AsrClientAdapter asrClient,
                                 MinioStorageClient minioStorageClient,
                                 MediaProcessingProperties properties,
                                 ObjectMapper objectMapper) {
        this.ffmpeg = ffmpeg;
        this.asrClient = asrClient;
        this.minioStorageClient = minioStorageClient;
        this.properties = properties;
        this.objectMapper = objectMapper;
    }

    /** 提取特征并写入 feature（meta / keyframes / sceneJson / ocrJson / transcriptText / timelineJson / featureVersion）。 */
    public void extractInto(VideoFeature feature, VideoAsset asset) {
        ffmpeg.withDownloadedVideo(asset.getFileUrl(), videoPath -> {
            Path frameDir = Files.createTempDirectory("video-frames-");
            try {
                analyze(feature, asset, videoPath, frameDir);
            } finally {
                FfmpegMediaAdapter.deleteRecursively(frameDir);
            }
            return null;
        });
    }

    private void analyze(VideoFeature feature, VideoAsset asset, Path videoPath, Path frameDir) {
        FfmpegMediaAdapter.ProbeResult probe = ffmpeg.probe(videoPath, asset.getFileUrl());
        VideoMeta meta = probe.meta();
        double duration = meta.durationMs() / 1000.0;
        double window = duration > 0 ? Math.min(duration, properties.getAnalysisWindowSeconds()) : properties.getAnalysisWindowSeconds();
        boolean truncated = duration > properties.getAnalysisWindowSeconds();

        List<Double> sceneChanges = detectScenes(videoPath, window);
        List<FrameSamplingPlan.Sample> plan = FrameSamplingPlan.plan(
                window,
                properties.getHookDenseSeconds(),
                properties.getHookFrameIntervalSeconds(),
                properties.getFrameIntervalSeconds(),
                sceneChanges,
                properties.getSceneMergeSeconds(),
                properties.getMaxKeyframes()
        );

        List<FrameResult> frames = extractFrames(asset.getId(), videoPath, frameDir, plan);
        AsrClientAdapter.AsrResult asr = asrClient.transcribe(videoPath, window, probe.hasAudio());

        feature.setMeta(meta);
        feature.setKeyframes(frames.stream().map(FrameResult::url).toList());
        feature.setSceneJson(toJson(buildScenes(sceneChanges, window, duration)));
        feature.setOcrJson(toJson(Map.of("ocr", mergeOcr(frames, window))));
        feature.setTranscriptText(asr.fullText());
        feature.setTimelineJson(toJson(buildTimeline(duration, window, truncated, sceneChanges.size(), frames, asr)));
        feature.setFeatureVersion(FEATURE_VERSION);
        log.info("Extracted features for video {}: window={}s frames={} scenes={} asr={}",
                asset.getId(), window, frames.size(), sceneChanges.size(), asr.status());
    }

    private List<Double> detectScenes(Path videoPath, double window) {
        try {
            return ffmpeg.detectSceneChanges(videoPath, window, properties.getSceneThreshold());
        } catch (RuntimeException ex) {
            // 场景检测失败不影响其它特征，按"无切换"处理
            log.warn("Scene detection failed: {}", ex.getMessage());
            return List.of();
        }
    }

    private List<FrameResult> extractFrames(String assetId, Path videoPath, Path frameDir, List<FrameSamplingPlan.Sample> plan) {
        int parallelism = Math.max(1, properties.getOcrParallelism());
        ExecutorService pool = Executors.newFixedThreadPool(parallelism);
        try {
            List<Future<FrameResult>> futures = new ArrayList<>();
            for (int i = 0; i < plan.size(); i++) {
                final int index = i + 1;
                final FrameSamplingPlan.Sample sample = plan.get(i);
                futures.add(pool.submit(() -> extractOne(assetId, videoPath, frameDir, index, sample)));
            }
            List<FrameResult> results = new ArrayList<>();
            for (Future<FrameResult> future : futures) {
                try {
                    FrameResult result = future.get();
                    if (result != null) {
                        results.add(result);
                    }
                } catch (ExecutionException ex) {
                    log.warn("Frame extraction failed: {}", ex.getCause() == null ? ex.getMessage() : ex.getCause().getMessage());
                }
            }
            return results;
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Frame extraction interrupted", ex);
        } finally {
            pool.shutdownNow();
        }
    }

    private FrameResult extractOne(String assetId, Path videoPath, Path frameDir, int index, FrameSamplingPlan.Sample sample) {
        Path framePath = frameDir.resolve(String.format("frame-%03d.jpg", index));
        if (!ffmpeg.extractFrameAt(videoPath, sample.seconds(), framePath)) {
            return null;
        }
        String ocrText = "";
        try {
            ocrText = ffmpeg.ocrImage(framePath);
        } catch (RuntimeException ex) {
            log.warn("OCR failed at {}s: {}", sample.seconds(), ex.getMessage());
        }
        String url = minioStorageClient.uploadFrame(framePath, assetId, index).publicUrl();
        return new FrameResult(index, sample.seconds(), sample.reason(), url, ocrText);
    }

    /** 连续帧上的相同字幕合并为一段 [start, end)，end 取下一采样点或窗口末尾。 */
    static List<Map<String, Object>> mergeOcr(List<FrameResult> frames, double window) {
        List<Map<String, Object>> items = new ArrayList<>();
        Map<String, Object> current = null;
        String currentKey = "";
        for (int i = 0; i < frames.size(); i++) {
            FrameResult frame = frames.get(i);
            double next = i + 1 < frames.size() ? frames.get(i + 1).seconds() : window;
            String key = comparableText(frame.ocrText());
            if (key.isEmpty()) {
                current = null;
                currentKey = "";
                continue;
            }
            if (current != null && sameText(currentKey, key)) {
                current.put("endSeconds", round(next));
                current.put("end", FfmpegMediaAdapter.formatTimestamp(next));
                current.put("timeRange", current.get("time") + "-" + FfmpegMediaAdapter.formatTimestamp(next));
                if (key.length() > currentKey.length()) {
                    current.put("text", frame.ocrText());
                    currentKey = key;
                }
                continue;
            }
            current = new LinkedHashMap<>();
            current.put("frameIndex", frame.index());
            current.put("time", FfmpegMediaAdapter.formatTimestamp(frame.seconds()));
            current.put("end", FfmpegMediaAdapter.formatTimestamp(next));
            current.put("timeRange", FfmpegMediaAdapter.formatTimestamp(frame.seconds()) + "-" + FfmpegMediaAdapter.formatTimestamp(next));
            current.put("startSeconds", round(frame.seconds()));
            current.put("endSeconds", round(next));
            current.put("text", frame.ocrText());
            currentKey = key;
            items.add(current);
        }
        return items;
    }

    static Map<String, Object> buildScenes(List<Double> changes, double window, double duration) {
        List<Map<String, Object>> scenes = new ArrayList<>();
        double start = 0;
        List<Double> bounds = new ArrayList<>(changes);
        bounds.add(window);
        for (Double bound : bounds) {
            if (bound - start < 0.2 && bound < window) {
                continue;
            }
            Map<String, Object> scene = new LinkedHashMap<>();
            scene.put("index", scenes.size() + 1);
            scene.put("start", FfmpegMediaAdapter.formatTimestamp(start));
            scene.put("end", FfmpegMediaAdapter.formatTimestamp(bound));
            scene.put("startSeconds", round(start));
            scene.put("endSeconds", round(bound));
            scene.put("durationSeconds", round(bound - start));
            scenes.add(scene);
            start = bound;
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("detected", true);
        result.put("durationSeconds", round(duration));
        result.put("analyzedSeconds", round(window));
        result.put("sceneCount", scenes.size());
        result.put("avgSceneSeconds", scenes.isEmpty() ? 0 : round(window / scenes.size()));
        result.put("scenes", scenes);
        return result;
    }

    private Map<String, Object> buildTimeline(double duration,
                                              double window,
                                              boolean truncated,
                                              int sceneChangeCount,
                                              List<FrameResult> frames,
                                              AsrClientAdapter.AsrResult asr) {
        List<Map<String, Object>> keyframes = new ArrayList<>();
        for (FrameResult frame : frames) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("index", frame.index());
            item.put("time", FfmpegMediaAdapter.formatTimestamp(frame.seconds()));
            item.put("seconds", round(frame.seconds()));
            item.put("reason", frame.reason());
            item.put("url", frame.url());
            keyframes.add(item);
        }
        List<Map<String, Object>> segments = new ArrayList<>();
        for (AsrClientAdapter.AsrSegment segment : asr.segments()) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("start", FfmpegMediaAdapter.formatTimestamp(segment.start()));
            item.put("end", FfmpegMediaAdapter.formatTimestamp(segment.end()));
            item.put("startSeconds", round(segment.start()));
            item.put("endSeconds", round(segment.end()));
            item.put("text", segment.text());
            segments.add(item);
        }
        Map<String, Object> transcript = new LinkedHashMap<>();
        transcript.put("status", asr.status());
        transcript.put("model", asr.model());
        if (asr.error() != null && !asr.error().isBlank()) {
            transcript.put("error", asr.error());
        }
        transcript.put("segments", segments);

        Map<String, Object> timeline = new LinkedHashMap<>();
        timeline.put("version", FEATURE_VERSION);
        timeline.put("durationSeconds", round(duration));
        timeline.put("analyzedSeconds", round(window));
        timeline.put("truncated", truncated);
        timeline.put("sceneChangeCount", sceneChangeCount);
        timeline.put("keyframes", keyframes);
        timeline.put("transcript", transcript);
        return timeline;
    }

    private static String comparableText(String text) {
        if (text == null) {
            return "";
        }
        return text.replaceAll("[\\s\\p{Punct}\\p{IsPunctuation}]", "");
    }

    /** OCR 有噪声：完全相同或一方包含另一方（较短的 >= 4 个字符）视为同一条字幕。 */
    private static boolean sameText(String left, String right) {
        if (left.equals(right)) {
            return true;
        }
        String shorter = left.length() <= right.length() ? left : right;
        String longer = shorter == left ? right : left;
        return shorter.length() >= 4 && longer.contains(shorter);
    }

    private static double round(double value) {
        return Math.round(value * 10.0) / 10.0;
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException ex) {
            throw new IllegalStateException("Failed to serialize media features", ex);
        }
    }

    record FrameResult(int index, double seconds, String reason, String url, String ocrText) {
    }
}
