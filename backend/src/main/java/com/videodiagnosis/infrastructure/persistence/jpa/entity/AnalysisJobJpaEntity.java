package com.videodiagnosis.infrastructure.persistence.jpa.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import jakarta.persistence.Version;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "analysis_job",
        indexes = {
                @Index(name = "idx_analysis_job_status", columnList = "status"),
                @Index(name = "idx_analysis_job_target_video_id", columnList = "target_video_id")
        }
)
public class AnalysisJobJpaEntity {

    @Id
    private String id;

    @Column(name = "job_key", unique = true, nullable = false)
    private String jobKey;

    @Column(name = "target_video_id", nullable = false)
    private String targetVideoId;

    // MySQL 单行上限 65535 字节：utf8mb4 下多个 varchar(4000)/varchar(2000) 会超限导致建表失败，长文本改为 LONGTEXT（行外存储）
    @Lob
    @Column(name = "reference_video_ids_json", columnDefinition = "LONGTEXT")
    private String referenceVideoIdsJson;

    @Column(nullable = false)
    private String status;

    private int progress;

    @Column(name = "current_stage")
    private String currentStage;

    @Lob
    @Column(name = "input_snapshot_json", columnDefinition = "LONGTEXT")
    private String inputSnapshotJson;

    @Lob
    @Column(name = "skill_version_snapshot_json", columnDefinition = "LONGTEXT")
    private String skillVersionSnapshotJson;

    @Column(name = "error_code")
    private String errorCode;

    @Lob
    @Column(name = "error_message", columnDefinition = "LONGTEXT")
    private String errorMessage;

    @Version
    private Long version;

    private int retryCount;

    private int maxRetryCount;

    private LocalDateTime nextRetryAt;

    @Lob
    @Column(name = "last_error", columnDefinition = "LONGTEXT")
    private String lastError;

    @Column(name = "current_agent_run_id")
    private String currentAgentRunId;

    private LocalDateTime agentStartedAt;

    private LocalDateTime agentTimeoutAt;

    @Column(name = "last_processed_agent_run_id")
    private String lastProcessedAgentRunId;

    private Integer lastResultVersion;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;

    private LocalDateTime startedAt;

    private LocalDateTime finishedAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getJobKey() { return jobKey; }
    public void setJobKey(String jobKey) { this.jobKey = jobKey; }
    public String getTargetVideoId() { return targetVideoId; }
    public void setTargetVideoId(String targetVideoId) { this.targetVideoId = targetVideoId; }
    public String getReferenceVideoIdsJson() { return referenceVideoIdsJson; }
    public void setReferenceVideoIdsJson(String referenceVideoIdsJson) { this.referenceVideoIdsJson = referenceVideoIdsJson; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public int getProgress() { return progress; }
    public void setProgress(int progress) { this.progress = progress; }
    public String getCurrentStage() { return currentStage; }
    public void setCurrentStage(String currentStage) { this.currentStage = currentStage; }
    public String getInputSnapshotJson() { return inputSnapshotJson; }
    public void setInputSnapshotJson(String inputSnapshotJson) { this.inputSnapshotJson = inputSnapshotJson; }
    public String getSkillVersionSnapshotJson() { return skillVersionSnapshotJson; }
    public void setSkillVersionSnapshotJson(String skillVersionSnapshotJson) { this.skillVersionSnapshotJson = skillVersionSnapshotJson; }
    public String getErrorCode() { return errorCode; }
    public void setErrorCode(String errorCode) { this.errorCode = errorCode; }
    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }
    public int getRetryCount() { return retryCount; }
    public void setRetryCount(int retryCount) { this.retryCount = retryCount; }
    public int getMaxRetryCount() { return maxRetryCount; }
    public void setMaxRetryCount(int maxRetryCount) { this.maxRetryCount = maxRetryCount; }
    public LocalDateTime getNextRetryAt() { return nextRetryAt; }
    public void setNextRetryAt(LocalDateTime nextRetryAt) { this.nextRetryAt = nextRetryAt; }
    public String getLastError() { return lastError; }
    public void setLastError(String lastError) { this.lastError = lastError; }
    public String getCurrentAgentRunId() { return currentAgentRunId; }
    public void setCurrentAgentRunId(String currentAgentRunId) { this.currentAgentRunId = currentAgentRunId; }
    public LocalDateTime getAgentStartedAt() { return agentStartedAt; }
    public void setAgentStartedAt(LocalDateTime agentStartedAt) { this.agentStartedAt = agentStartedAt; }
    public LocalDateTime getAgentTimeoutAt() { return agentTimeoutAt; }
    public void setAgentTimeoutAt(LocalDateTime agentTimeoutAt) { this.agentTimeoutAt = agentTimeoutAt; }
    public String getLastProcessedAgentRunId() { return lastProcessedAgentRunId; }
    public void setLastProcessedAgentRunId(String lastProcessedAgentRunId) { this.lastProcessedAgentRunId = lastProcessedAgentRunId; }
    public Integer getLastResultVersion() { return lastResultVersion; }
    public void setLastResultVersion(Integer lastResultVersion) { this.lastResultVersion = lastResultVersion; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
    public LocalDateTime getStartedAt() { return startedAt; }
    public void setStartedAt(LocalDateTime startedAt) { this.startedAt = startedAt; }
    public LocalDateTime getFinishedAt() { return finishedAt; }
    public void setFinishedAt(LocalDateTime finishedAt) { this.finishedAt = finishedAt; }
}
