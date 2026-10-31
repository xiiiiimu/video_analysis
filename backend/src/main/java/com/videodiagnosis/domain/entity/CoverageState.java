package com.videodiagnosis.domain.entity;

import com.videodiagnosis.types.enums.AnalysisDimensionEnum;

import java.time.LocalDateTime;

public class CoverageState {

    private String id;
    private String jobId;
    private AnalysisDimensionEnum dimension;
    private String state;
    private String reason;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getJobId() {
        return jobId;
    }

    public void setJobId(String jobId) {
        this.jobId = jobId;
    }

    public AnalysisDimensionEnum getDimension() {
        return dimension;
    }

    public void setDimension(AnalysisDimensionEnum dimension) {
        this.dimension = dimension;
    }

    public String getState() {
        return state;
    }

    public void setState(String state) {
        this.state = state;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
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
