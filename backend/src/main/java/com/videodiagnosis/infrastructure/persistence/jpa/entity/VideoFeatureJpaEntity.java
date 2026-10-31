package com.videodiagnosis.infrastructure.persistence.jpa.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;

import java.time.LocalDateTime;

@Entity
@Table(name = "video_feature")
public class VideoFeatureJpaEntity {

    @Id
    private String id;
    private String videoAssetId;
    private String jobId;
    // ASR 文本 / 关键帧 / OCR 等都可能远超 varchar(255)，MySQL 严格模式下会 Data too long
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String transcriptText;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String keyframesJson;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String sceneJson;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String ocrJson;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String metaJson;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String timelineJson;
    private String featureVersion;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getVideoAssetId() { return videoAssetId; }
    public void setVideoAssetId(String videoAssetId) { this.videoAssetId = videoAssetId; }
    public String getJobId() { return jobId; }
    public void setJobId(String jobId) { this.jobId = jobId; }
    public String getTranscriptText() { return transcriptText; }
    public void setTranscriptText(String transcriptText) { this.transcriptText = transcriptText; }
    public String getKeyframesJson() { return keyframesJson; }
    public void setKeyframesJson(String keyframesJson) { this.keyframesJson = keyframesJson; }
    public String getSceneJson() { return sceneJson; }
    public void setSceneJson(String sceneJson) { this.sceneJson = sceneJson; }
    public String getOcrJson() { return ocrJson; }
    public void setOcrJson(String ocrJson) { this.ocrJson = ocrJson; }
    public String getTimelineJson() { return timelineJson; }
    public void setTimelineJson(String timelineJson) { this.timelineJson = timelineJson; }
    public String getMetaJson() { return metaJson; }
    public void setMetaJson(String metaJson) { this.metaJson = metaJson; }
    public String getFeatureVersion() { return featureVersion; }
    public void setFeatureVersion(String featureVersion) { this.featureVersion = featureVersion; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}