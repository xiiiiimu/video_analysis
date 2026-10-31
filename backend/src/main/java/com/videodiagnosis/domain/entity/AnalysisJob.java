package com.videodiagnosis.domain.entity;

import com.videodiagnosis.domain.exception.InvalidJobStateTransitionException;
import com.videodiagnosis.types.enums.JobStatusEnum;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;

public class AnalysisJob {

    private String id;
    private String jobKey;
    private String targetVideoId;
    private List<String> referenceVideoIds = new ArrayList<>();
    private JobStatusEnum status;
    private int progress;
    private String currentStage;
    private String inputSnapshotJson;
    private String skillVersionSnapshotJson;
    private String errorCode;
    private String errorMessage;
    private Long version;
    private int retryCount;
    private int maxRetryCount = 3;
    private LocalDateTime nextRetryAt;
    private String lastError;
    private String currentAgentRunId;
    private LocalDateTime agentStartedAt;
    private LocalDateTime agentTimeoutAt;
    private String lastProcessedAgentRunId;
    private Integer lastResultVersion;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private LocalDateTime startedAt;
    private LocalDateTime finishedAt;

    public void initializeCreated() {
        this.status = JobStatusEnum.CREATED;
        this.currentStage = "CREATED";
        this.progress = 0;
        LocalDateTime now = LocalDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    public void startPreprocessing() {
        transitionTo(JobStatusEnum.PREPROCESSING, EnumSet.of(JobStatusEnum.CREATED, JobStatusEnum.PENDING));
        this.currentStage = "PREPROCESSING";
        this.progress = 20;
        if (this.startedAt == null) {
            this.startedAt = LocalDateTime.now();
        }
        this.updatedAt = LocalDateTime.now();
    }

    public void markEvidenceReady() {
        transitionTo(JobStatusEnum.EVIDENCE_READY, EnumSet.of(JobStatusEnum.CREATED, JobStatusEnum.PENDING, JobStatusEnum.PREPROCESSING));
        this.currentStage = "EVIDENCE_READY";
        this.progress = Math.max(this.progress, 35);
        this.updatedAt = LocalDateTime.now();
    }

    public void waitForAgent(LocalDateTime nextRetryAt) {
        transitionTo(JobStatusEnum.WAITING_AGENT, EnumSet.of(JobStatusEnum.CREATED, JobStatusEnum.PENDING, JobStatusEnum.EVIDENCE_READY, JobStatusEnum.RETRYING));
        this.currentStage = "WAITING_AGENT";
        this.progress = Math.max(this.progress, 40);
        this.nextRetryAt = nextRetryAt == null ? LocalDateTime.now() : nextRetryAt;
        this.updatedAt = LocalDateTime.now();
    }

    public void markAgentRunning(String agentRunId, LocalDateTime timeoutAt) {
        transitionTo(JobStatusEnum.AGENT_RUNNING, EnumSet.of(JobStatusEnum.WAITING_AGENT, JobStatusEnum.RETRYING));
        this.currentAgentRunId = agentRunId;
        this.agentStartedAt = LocalDateTime.now();
        this.agentTimeoutAt = timeoutAt;
        this.currentStage = "AGENT_RUNNING";
        this.progress = Math.max(this.progress, 55);
        if (this.startedAt == null) {
            this.startedAt = LocalDateTime.now();
        }
        this.updatedAt = LocalDateTime.now();
    }

    public void startResultProcessing() {
        transitionTo(JobStatusEnum.RESULT_PROCESSING, EnumSet.of(JobStatusEnum.AGENT_RUNNING));
        this.currentStage = "RESULT_PROCESSING";
        this.progress = Math.max(this.progress, 85);
        this.updatedAt = LocalDateTime.now();
    }

    public void complete(String agentRunId, Integer resultVersion) {
        transitionTo(JobStatusEnum.COMPLETED, EnumSet.of(JobStatusEnum.RESULT_PROCESSING, JobStatusEnum.AGENT_RUNNING, JobStatusEnum.RUNNING, JobStatusEnum.ANALYZING));
        this.lastProcessedAgentRunId = agentRunId;
        this.lastResultVersion = resultVersion;
        this.currentStage = "COMPLETED";
        this.progress = 100;
        this.finishedAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    public void retry(String errorMessage, LocalDateTime nextRetryAt) {
        transitionTo(JobStatusEnum.RETRYING, EnumSet.of(JobStatusEnum.AGENT_RUNNING, JobStatusEnum.WAITING_AGENT, JobStatusEnum.RETRYING));
        this.retryCount++;
        this.lastError = errorMessage;
        this.errorMessage = errorMessage;
        this.nextRetryAt = nextRetryAt;
        this.currentStage = "RETRYING";
        this.progress = Math.min(this.progress, 50);
        this.currentAgentRunId = null;
        this.agentTimeoutAt = null;
        this.updatedAt = LocalDateTime.now();
    }

    public boolean canRetry() {
        return retryCount < maxRetryCount;
    }

    public boolean canAcceptAgentResult(String agentRunId, Integer resultVersion, LocalDateTime now) {
        if (status != JobStatusEnum.AGENT_RUNNING) {
            return false;
        }
        if (agentTimeoutAt != null && now != null && agentTimeoutAt.isBefore(now)) {
            return false;
        }
        if (agentRunId != null && !agentRunId.isBlank() && currentAgentRunId != null && !currentAgentRunId.equals(agentRunId)) {
            return false;
        }
        if (lastResultVersion != null && resultVersion != null && resultVersion <= lastResultVersion) {
            return false;
        }
        return status != JobStatusEnum.COMPLETED && status != JobStatusEnum.FAILED;
    }

    public void markRunning() {
        transitionTo(JobStatusEnum.RUNNING, EnumSet.of(JobStatusEnum.PENDING, JobStatusEnum.CREATED));
        this.currentStage = "RUNNING";
        this.progress = 10;
        if (this.startedAt == null) {
            this.startedAt = LocalDateTime.now();
        }
        this.updatedAt = LocalDateTime.now();
    }

    public void markPreprocessing() {
        startPreprocessing();
    }

    public void markAnalyzing() {
        transitionTo(JobStatusEnum.ANALYZING, EnumSet.of(JobStatusEnum.PREPROCESSING, JobStatusEnum.EVIDENCE_READY, JobStatusEnum.RUNNING));
        this.currentStage = "ANALYZING";
        this.progress = 60;
        this.updatedAt = LocalDateTime.now();
    }

    public void markCompleted() {
        complete(currentAgentRunId, lastResultVersion == null ? 1 : lastResultVersion + 1);
    }

    public void markFailed(String errorCode, String errorMessage) {
        if (this.status == JobStatusEnum.COMPLETED) {
            throw new InvalidJobStateTransitionException(this.status, JobStatusEnum.FAILED);
        }
        this.status = JobStatusEnum.FAILED;
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
        this.lastError = errorMessage;
        this.currentStage = "FAILED";
        this.finishedAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    private void transitionTo(JobStatusEnum target, EnumSet<JobStatusEnum> allowedSources) {
        if (this.status != null && !allowedSources.contains(this.status)) {
            throw new InvalidJobStateTransitionException(this.status, target);
        }
        this.status = target;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getJobKey() {
        return jobKey;
    }

    public void setJobKey(String jobKey) {
        this.jobKey = jobKey;
    }

    public String getTargetVideoId() {
        return targetVideoId;
    }

    public void setTargetVideoId(String targetVideoId) {
        this.targetVideoId = targetVideoId;
    }

    public List<String> getReferenceVideoIds() {
        return referenceVideoIds;
    }

    public void setReferenceVideoIds(List<String> referenceVideoIds) {
        this.referenceVideoIds = referenceVideoIds == null ? new ArrayList<>() : new ArrayList<>(referenceVideoIds);
    }

    public JobStatusEnum getStatus() {
        return status;
    }

    public void setStatus(JobStatusEnum status) {
        this.status = status;
    }

    public int getProgress() {
        return progress;
    }

    public void setProgress(int progress) {
        this.progress = progress;
    }

    public String getCurrentStage() {
        return currentStage;
    }

    public void setCurrentStage(String currentStage) {
        this.currentStage = currentStage;
    }

    public String getInputSnapshotJson() {
        return inputSnapshotJson;
    }

    public void setInputSnapshotJson(String inputSnapshotJson) {
        this.inputSnapshotJson = inputSnapshotJson;
    }

    public String getSkillVersionSnapshotJson() {
        return skillVersionSnapshotJson;
    }

    public void setSkillVersionSnapshotJson(String skillVersionSnapshotJson) {
        this.skillVersionSnapshotJson = skillVersionSnapshotJson;
    }

    public String getErrorCode() {
        return errorCode;
    }

    public void setErrorCode(String errorCode) {
        this.errorCode = errorCode;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public Long getVersion() {
        return version;
    }

    public void setVersion(Long version) {
        this.version = version;
    }

    public int getRetryCount() {
        return retryCount;
    }

    public void setRetryCount(int retryCount) {
        this.retryCount = retryCount;
    }

    public int getMaxRetryCount() {
        return maxRetryCount;
    }

    public void setMaxRetryCount(int maxRetryCount) {
        this.maxRetryCount = maxRetryCount;
    }

    public LocalDateTime getNextRetryAt() {
        return nextRetryAt;
    }

    public void setNextRetryAt(LocalDateTime nextRetryAt) {
        this.nextRetryAt = nextRetryAt;
    }

    public String getLastError() {
        return lastError;
    }

    public void setLastError(String lastError) {
        this.lastError = lastError;
    }

    public String getCurrentAgentRunId() {
        return currentAgentRunId;
    }

    public void setCurrentAgentRunId(String currentAgentRunId) {
        this.currentAgentRunId = currentAgentRunId;
    }

    public LocalDateTime getAgentStartedAt() {
        return agentStartedAt;
    }

    public void setAgentStartedAt(LocalDateTime agentStartedAt) {
        this.agentStartedAt = agentStartedAt;
    }

    public LocalDateTime getAgentTimeoutAt() {
        return agentTimeoutAt;
    }

    public void setAgentTimeoutAt(LocalDateTime agentTimeoutAt) {
        this.agentTimeoutAt = agentTimeoutAt;
    }

    public String getLastProcessedAgentRunId() {
        return lastProcessedAgentRunId;
    }

    public void setLastProcessedAgentRunId(String lastProcessedAgentRunId) {
        this.lastProcessedAgentRunId = lastProcessedAgentRunId;
    }

    public Integer getLastResultVersion() {
        return lastResultVersion;
    }

    public void setLastResultVersion(Integer lastResultVersion) {
        this.lastResultVersion = lastResultVersion;
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

    public LocalDateTime getStartedAt() {
        return startedAt;
    }

    public void setStartedAt(LocalDateTime startedAt) {
        this.startedAt = startedAt;
    }

    public LocalDateTime getFinishedAt() {
        return finishedAt;
    }

    public void setFinishedAt(LocalDateTime finishedAt) {
        this.finishedAt = finishedAt;
    }
}
