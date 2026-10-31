package com.videodiagnosis.domain.entity;

import com.videodiagnosis.domain.valueobject.Evidence;
import com.videodiagnosis.domain.valueobject.Hypothesis;
import com.videodiagnosis.types.enums.AnalysisDimensionEnum;
import com.videodiagnosis.types.enums.PriorityEnum;

import java.time.LocalDateTime;

public class Finding {

    private String id;
    private String jobId;
    private AnalysisDimensionEnum dimension;
    private PriorityEnum priority;
    private String status;
    private String observation;
    private Evidence targetEvidence;
    private Evidence referenceEvidence;
    private String differenceText;
    private Hypothesis hypothesis;
    private double confidence;
    private String source;
    private String counterEvidence;
    private String suggestedAction;
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

    public PriorityEnum getPriority() {
        return priority;
    }

    public void setPriority(PriorityEnum priority) {
        this.priority = priority;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getObservation() {
        return observation;
    }

    public void setObservation(String observation) {
        this.observation = observation;
    }

    public Evidence getTargetEvidence() {
        return targetEvidence;
    }

    public void setTargetEvidence(Evidence targetEvidence) {
        this.targetEvidence = targetEvidence;
    }

    public Evidence getReferenceEvidence() {
        return referenceEvidence;
    }

    public void setReferenceEvidence(Evidence referenceEvidence) {
        this.referenceEvidence = referenceEvidence;
    }

    public String getDifferenceText() {
        return differenceText;
    }

    public void setDifferenceText(String differenceText) {
        this.differenceText = differenceText;
    }

    public Hypothesis getHypothesis() {
        return hypothesis;
    }

    public void setHypothesis(Hypothesis hypothesis) {
        this.hypothesis = hypothesis;
    }

    public double getConfidence() {
        return confidence;
    }

    public void setConfidence(double confidence) {
        this.confidence = confidence;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public String getCounterEvidence() {
        return counterEvidence;
    }

    public void setCounterEvidence(String counterEvidence) {
        this.counterEvidence = counterEvidence;
    }

    public String getSuggestedAction() {
        return suggestedAction;
    }

    public void setSuggestedAction(String suggestedAction) {
        this.suggestedAction = suggestedAction;
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
