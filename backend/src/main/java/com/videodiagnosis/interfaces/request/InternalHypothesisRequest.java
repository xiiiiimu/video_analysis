package com.videodiagnosis.interfaces.request;

import jakarta.validation.constraints.NotBlank;

import java.util.List;

/**
 * agent-service 提交的单条诊断结论。
 *
 * <p>skillKey / outcome / findingType / idempotencyKey 为新增的可选字段：
 * outcome 区分 FINDING（形成结论）与 ABSTAIN（证据不足未下结论）；
 * idempotencyKey 用于逐条保存时去重（批量接口不可用时的回退路径）；
 * priority（P0/P1/P2）由 agent 按合成排序给出，缺省时按置信度判定。
 */
public record InternalHypothesisRequest(
        @NotBlank String jobId,
        @NotBlank String dimension,
        @NotBlank String observation,
        String differenceText,
        String hypothesisText,
        String suggestedAction,
        List<String> evidenceRefs,
        List<String> videoEvidenceRefs,
        List<String> knowledgeEvidenceRefs,
        List<String> targetFrameRefs,
        List<String> referenceFrameRefs,
        String counterEvidence,
        Double confidence,
        String skillKey,
        String outcome,
        String findingType,
        String idempotencyKey,
        String priority
) {
    public InternalHypothesisRequest(String jobId,
                                     String dimension,
                                     String observation,
                                     String differenceText,
                                     String hypothesisText,
                                     String suggestedAction,
                                     List<String> evidenceRefs,
                                     List<String> videoEvidenceRefs,
                                     List<String> knowledgeEvidenceRefs,
                                     List<String> targetFrameRefs,
                                     List<String> referenceFrameRefs,
                                     String counterEvidence,
                                     Double confidence,
                                     String skillKey,
                                     String outcome,
                                     String findingType,
                                     String idempotencyKey) {
        this(jobId, dimension, observation, differenceText, hypothesisText, suggestedAction,
                evidenceRefs, videoEvidenceRefs, knowledgeEvidenceRefs, targetFrameRefs, referenceFrameRefs,
                counterEvidence, confidence, skillKey, outcome, findingType, idempotencyKey, null);
    }

    public InternalHypothesisRequest(String jobId,
                                     String dimension,
                                     String observation,
                                     String differenceText,
                                     String hypothesisText,
                                     String suggestedAction,
                                     List<String> evidenceRefs,
                                     List<String> videoEvidenceRefs,
                                     List<String> knowledgeEvidenceRefs,
                                     List<String> targetFrameRefs,
                                     List<String> referenceFrameRefs,
                                     String counterEvidence,
                                     Double confidence) {
        this(jobId, dimension, observation, differenceText, hypothesisText, suggestedAction,
                evidenceRefs, videoEvidenceRefs, knowledgeEvidenceRefs, targetFrameRefs, referenceFrameRefs,
                counterEvidence, confidence, null, null, null, null);
    }

    public InternalHypothesisRequest(String jobId,
                                     String dimension,
                                     String observation,
                                     String differenceText,
                                     String hypothesisText,
                                     String suggestedAction,
                                     List<String> targetFrameRefs,
                                     List<String> referenceFrameRefs,
                                     String counterEvidence,
                                     Double confidence) {
        this(jobId, dimension, observation, differenceText, hypothesisText, suggestedAction,
                null, null, null, targetFrameRefs, referenceFrameRefs, counterEvidence, confidence,
                null, null, null, null);
    }

    public boolean isAbstain() {
        return "ABSTAIN".equalsIgnoreCase(outcome);
    }
}
