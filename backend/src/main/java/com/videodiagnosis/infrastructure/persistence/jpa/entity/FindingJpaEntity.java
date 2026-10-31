package com.videodiagnosis.infrastructure.persistence.jpa.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "finding",
        indexes = {
                @Index(name = "idx_finding_job_id", columnList = "job_id")
        }
)
public class FindingJpaEntity {

    // 文本与证据 JSON 字段使用 LONGTEXT：默认 varchar(255) 在 MySQL 严格模式下会因证据引用较多而写入失败。
    // 注意：Hibernate 6 在 MySQL 上会把未指定长度的 @Lob 建成 tinytext（255 字节），必须显式 columnDefinition。
    // 已有 MySQL 表不会被 ddl-auto=update 自动改列类型，迁移 SQL 见 docs/14-orchestration-refactor.md。

    @Id
    private String id;
    private String jobId;
    private String dimension;
    private String priority;
    private String status;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String observation;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String targetEvidenceJson;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String referenceEvidenceJson;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String differenceText;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String hypothesisText;
    private double confidence;
    private String source;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String counterEvidence;
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String suggestedAction;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getJobId() { return jobId; }
    public void setJobId(String jobId) { this.jobId = jobId; }
    public String getDimension() { return dimension; }
    public void setDimension(String dimension) { this.dimension = dimension; }
    public String getPriority() { return priority; }
    public void setPriority(String priority) { this.priority = priority; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getObservation() { return observation; }
    public void setObservation(String observation) { this.observation = observation; }
    public String getTargetEvidenceJson() { return targetEvidenceJson; }
    public void setTargetEvidenceJson(String targetEvidenceJson) { this.targetEvidenceJson = targetEvidenceJson; }
    public String getReferenceEvidenceJson() { return referenceEvidenceJson; }
    public void setReferenceEvidenceJson(String referenceEvidenceJson) { this.referenceEvidenceJson = referenceEvidenceJson; }
    public String getDifferenceText() { return differenceText; }
    public void setDifferenceText(String differenceText) { this.differenceText = differenceText; }
    public String getHypothesisText() { return hypothesisText; }
    public void setHypothesisText(String hypothesisText) { this.hypothesisText = hypothesisText; }
    public double getConfidence() { return confidence; }
    public void setConfidence(double confidence) { this.confidence = confidence; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public String getCounterEvidence() { return counterEvidence; }
    public void setCounterEvidence(String counterEvidence) { this.counterEvidence = counterEvidence; }
    public String getSuggestedAction() { return suggestedAction; }
    public void setSuggestedAction(String suggestedAction) { this.suggestedAction = suggestedAction; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
