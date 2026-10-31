package com.videodiagnosis.infrastructure.persistence.jpa.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.LocalDateTime;

/**
 * agent-service 结论保存记录：按 idempotencyKey 去重，并保存跨维度合成结果（synthesis）。
 */
@Entity
@Table(
        name = "diagnosis_result_record",
        uniqueConstraints = {
                @UniqueConstraint(name = "uk_diagnosis_result_idempotency", columnNames = {"idempotency_key"})
        },
        indexes = {
                @Index(name = "idx_diagnosis_result_job_id", columnList = "job_id")
        }
)
public class DiagnosisResultRecordJpaEntity {

    @Id
    private String id;

    @Column(name = "job_id", nullable = false)
    private String jobId;

    @Column(name = "agent_run_id")
    private String agentRunId;

    @Column(name = "result_version")
    private Integer resultVersion;

    @Column(name = "idempotency_key", nullable = false, length = 191)
    private String idempotencyKey;

    @Lob
    @Column(name = "finding_ids_json", columnDefinition = "LONGTEXT")
    private String findingIdsJson;

    @Lob
    @Column(name = "synthesis_json", columnDefinition = "LONGTEXT")
    private String synthesisJson;

    private LocalDateTime createdAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getJobId() { return jobId; }
    public void setJobId(String jobId) { this.jobId = jobId; }
    public String getAgentRunId() { return agentRunId; }
    public void setAgentRunId(String agentRunId) { this.agentRunId = agentRunId; }
    public Integer getResultVersion() { return resultVersion; }
    public void setResultVersion(Integer resultVersion) { this.resultVersion = resultVersion; }
    public String getIdempotencyKey() { return idempotencyKey; }
    public void setIdempotencyKey(String idempotencyKey) { this.idempotencyKey = idempotencyKey; }
    public String getFindingIdsJson() { return findingIdsJson; }
    public void setFindingIdsJson(String findingIdsJson) { this.findingIdsJson = findingIdsJson; }
    public String getSynthesisJson() { return synthesisJson; }
    public void setSynthesisJson(String synthesisJson) { this.synthesisJson = synthesisJson; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
