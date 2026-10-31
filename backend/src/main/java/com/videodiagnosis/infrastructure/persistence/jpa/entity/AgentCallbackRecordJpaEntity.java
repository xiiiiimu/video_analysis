package com.videodiagnosis.infrastructure.persistence.jpa.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "agent_callback_record",
        uniqueConstraints = {
                @UniqueConstraint(name = "uk_agent_callback_run_version", columnNames = {"agent_run_id", "result_version"})
        }
)
public class AgentCallbackRecordJpaEntity {

    @Id
    private String id;

    @Column(name = "job_id", nullable = false)
    private String jobId;

    @Column(name = "agent_run_id", nullable = false)
    private String agentRunId;

    @Column(name = "result_version", nullable = false)
    private Integer resultVersion;

    private LocalDateTime processedAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getJobId() { return jobId; }
    public void setJobId(String jobId) { this.jobId = jobId; }
    public String getAgentRunId() { return agentRunId; }
    public void setAgentRunId(String agentRunId) { this.agentRunId = agentRunId; }
    public Integer getResultVersion() { return resultVersion; }
    public void setResultVersion(Integer resultVersion) { this.resultVersion = resultVersion; }
    public LocalDateTime getProcessedAt() { return processedAt; }
    public void setProcessedAt(LocalDateTime processedAt) { this.processedAt = processedAt; }
}
