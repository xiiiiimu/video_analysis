package com.videodiagnosis.domain.entity;

import com.videodiagnosis.domain.valueobject.VideoMeta;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class VideoFeature {

    private static final Pattern OCR_TEXT_PATTERN = Pattern.compile("\"text\"\\s*:\\s*\"((?:\\\\.|[^\"\\\\])*)\"");

    private String id;
    private String videoAssetId;
    private String jobId;
    private String transcriptText;
    private List<String> keyframes = new ArrayList<>();
    private String sceneJson;
    private String ocrJson;
    /** 带时间戳的时间轴（关键帧 / 转写分段 / 截断信息），v0.2 起提供。 */
    private String timelineJson;
    private VideoMeta meta;
    private String featureVersion;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getVideoAssetId() {
        return videoAssetId;
    }

    public void setVideoAssetId(String videoAssetId) {
        this.videoAssetId = videoAssetId;
    }

    public String getJobId() {
        return jobId;
    }

    public void setJobId(String jobId) {
        this.jobId = jobId;
    }

    public String getTranscriptText() {
        return transcriptText;
    }

    public void setTranscriptText(String transcriptText) {
        this.transcriptText = transcriptText;
    }

    public String getTextForDiagnosis() {
        if (transcriptText != null && !transcriptText.isBlank()) {
            return transcriptText;
        }
        if (ocrJson == null || ocrJson.isBlank()) {
            return "";
        }
        List<String> texts = new ArrayList<>();
        Matcher matcher = OCR_TEXT_PATTERN.matcher(ocrJson);
        while (matcher.find()) {
            String text = unescapeJsonText(matcher.group(1)).trim();
            if (!text.isBlank()) {
                texts.add(text);
            }
        }
        return String.join(" ", texts);
    }

    public List<String> getKeyframes() {
        return keyframes;
    }

    public void setKeyframes(List<String> keyframes) {
        this.keyframes = keyframes == null ? new ArrayList<>() : new ArrayList<>(keyframes);
    }

    public String getSceneJson() {
        return sceneJson;
    }

    public void setSceneJson(String sceneJson) {
        this.sceneJson = sceneJson;
    }

    public String getOcrJson() {
        return ocrJson;
    }

    public void setOcrJson(String ocrJson) {
        this.ocrJson = ocrJson;
    }

    public String getTimelineJson() {
        return timelineJson;
    }

    public void setTimelineJson(String timelineJson) {
        this.timelineJson = timelineJson;
    }

    public VideoMeta getMeta() {
        return meta;
    }

    public void setMeta(VideoMeta meta) {
        this.meta = meta;
    }

    public String getFeatureVersion() {
        return featureVersion;
    }

    public void setFeatureVersion(String featureVersion) {
        this.featureVersion = featureVersion;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    private String unescapeJsonText(String text) {
        return text.replace("\\n", " ")
                .replace("\\r", " ")
                .replace("\\t", " ")
                .replace("\\\"", "\"")
                .replace("\\\\", "\\");
    }
}
