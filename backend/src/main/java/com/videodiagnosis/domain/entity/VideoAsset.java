package com.videodiagnosis.domain.entity;

import com.videodiagnosis.domain.valueobject.VideoMeta;
import com.videodiagnosis.types.enums.VideoStatusEnum;

import java.time.LocalDateTime;

public class VideoAsset {

    private String id;
    private String ownerId;
    private String role;
    private String title;
    private String description;
    private String coverUrl;
    private String fileUrl;
    private long fileSize;
    private long durationMs;
    private String mimeType;
    private VideoStatusEnum status;
    private VideoMeta meta;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public void markReady(VideoMeta meta) {
        this.meta = meta;
        this.durationMs = meta.durationMs();
        this.mimeType = meta.mimeType();
        this.status = VideoStatusEnum.READY;
        this.updatedAt = LocalDateTime.now();
    }

    public void markProcessing() {
        this.status = VideoStatusEnum.PROCESSING;
        this.updatedAt = LocalDateTime.now();
    }

    public void markProcessed() {
        this.status = VideoStatusEnum.PROCESSED;
        this.updatedAt = LocalDateTime.now();
    }

    public void markFailed() {
        this.status = VideoStatusEnum.FAILED;
        this.updatedAt = LocalDateTime.now();
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getOwnerId() {
        return ownerId;
    }

    public void setOwnerId(String ownerId) {
        this.ownerId = ownerId;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getCoverUrl() {
        return coverUrl;
    }

    public void setCoverUrl(String coverUrl) {
        this.coverUrl = coverUrl;
    }

    public String getFileUrl() {
        return fileUrl;
    }

    public void setFileUrl(String fileUrl) {
        this.fileUrl = fileUrl;
    }

    public long getFileSize() {
        return fileSize;
    }

    public void setFileSize(long fileSize) {
        this.fileSize = fileSize;
    }

    public long getDurationMs() {
        return durationMs;
    }

    public void setDurationMs(long durationMs) {
        this.durationMs = durationMs;
    }

    public String getMimeType() {
        return mimeType;
    }

    public void setMimeType(String mimeType) {
        this.mimeType = mimeType;
    }

    public VideoStatusEnum getStatus() {
        return status;
    }

    public void setStatus(VideoStatusEnum status) {
        this.status = status;
    }

    public VideoMeta getMeta() {
        return meta;
    }

    public void setMeta(VideoMeta meta) {
        this.meta = meta;
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
}
