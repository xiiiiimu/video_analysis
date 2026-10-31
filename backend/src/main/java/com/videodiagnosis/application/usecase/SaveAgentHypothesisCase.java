package com.videodiagnosis.application.usecase;

import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.domain.repository.FindingRepository;
import com.videodiagnosis.domain.valueobject.Evidence;
import com.videodiagnosis.domain.valueobject.Hypothesis;
import com.videodiagnosis.infrastructure.persistence.repository.DiagnosisResultRecordRepository;
import com.videodiagnosis.interfaces.request.InternalHypothesisRequest;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import com.videodiagnosis.types.enums.AnalysisDimensionEnum;
import com.videodiagnosis.types.enums.PriorityEnum;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * 持久化 agent-service 提交的诊断假设（映射为 Finding 落库，不重复领域启发式规则）。
 *
 * <p>逐条保存接口：批量接口 {@link SaveDiagnosisResultCase} 不可用时 agent-service 的回退路径。
 * 请求带 idempotencyKey 时按 key 去重，重复提交返回第一次保存的 Finding id。
 */
@Component
public class SaveAgentHypothesisCase {

    public static final String STATUS_AGENT = "agent";
    public static final String STATUS_AGENT_ABSTAIN = "agent_abstain";

    private final AnalysisJobRepository analysisJobRepository;
    private final FindingRepository findingRepository;
    private final DiagnosisResultRecordRepository resultRecordRepository;

    public SaveAgentHypothesisCase(AnalysisJobRepository analysisJobRepository,
                                   FindingRepository findingRepository,
                                   DiagnosisResultRecordRepository resultRecordRepository) {
        this.analysisJobRepository = analysisJobRepository;
        this.findingRepository = findingRepository;
        this.resultRecordRepository = resultRecordRepository;
    }

    @Transactional
    public Finding execute(InternalHypothesisRequest request) {
        requireJob(request.jobId());

        Optional<DiagnosisResultRecordRepository.StoredResult> existing =
                resultRecordRepository.findByIdempotencyKey(request.idempotencyKey());
        if (existing.isPresent() && !existing.get().findingIds().isEmpty()) {
            Finding duplicate = new Finding();
            duplicate.setId(existing.get().findingIds().get(0));
            duplicate.setJobId(request.jobId());
            return duplicate;
        }

        Finding saved = findingRepository.save(toFinding(request));
        if (request.idempotencyKey() != null && !request.idempotencyKey().isBlank()) {
            resultRecordRepository.save(request.jobId(), null, null, request.idempotencyKey(), List.of(saved.getId()), null);
        }
        return saved;
    }

    public void requireJob(String jobId) {
        analysisJobRepository.findById(jobId)
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.JOB_NOT_FOUND, "Analysis job not found: " + jobId));
    }

    /**
     * 把一条 agent 结论映射为 Finding（不落库）。批量保存与逐条保存共用。
     */
    public Finding toFinding(InternalHypothesisRequest request) {
        Finding finding = new Finding();
        finding.setId(UUID.randomUUID().toString());
        finding.setJobId(request.jobId());
        finding.setDimension(parseDimension(request.dimension()));
        finding.setPriority(resolvePriority(request.priority(), request.confidence()));
        // ABSTAIN（证据不足未下结论）单独标记，前端/报表可以与正式结论区分展示
        finding.setStatus(request.isAbstain() ? STATUS_AGENT_ABSTAIN : STATUS_AGENT);
        finding.setObservation(request.observation());
        finding.setDifferenceText(request.differenceText());
        finding.setHypothesis(request.hypothesisText() == null ? null : new Hypothesis(request.hypothesisText()));
        finding.setSuggestedAction(request.suggestedAction());
        finding.setTargetEvidence(new Evidence(
                firstNonEmpty(request.videoEvidenceRefs(), request.evidenceRefs(), request.targetFrameRefs()),
                List.of(),
                safeList(request.knowledgeEvidenceRefs())
        ));
        finding.setReferenceEvidence(new Evidence(
                List.of(),
                safeList(request.referenceFrameRefs()),
                List.of()
        ));
        finding.setConfidence(request.confidence() == null ? 0.75 : request.confidence());
        finding.setSource("agent-service");
        finding.setCounterEvidence(request.counterEvidence());
        finding.setCreatedAt(LocalDateTime.now());
        finding.setUpdatedAt(LocalDateTime.now());
        return finding;
    }

    private AnalysisDimensionEnum parseDimension(String dimension) {
        try {
            return AnalysisDimensionEnum.valueOf(dimension);
        } catch (IllegalArgumentException | NullPointerException ex) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, "Unknown analysis dimension: " + dimension);
        }
    }

    /**
     * agent 按合成排序给出的优先级优先（与 /synthesis 的排序一致）；
     * 旧版 agent 不传时沿用置信度规则。
     */
    private PriorityEnum resolvePriority(String priority, Double confidence) {
        if (priority != null && !priority.isBlank()) {
            try {
                return PriorityEnum.valueOf(priority.trim().toUpperCase());
            } catch (IllegalArgumentException ignored) {
                // 未知取值：回退到置信度规则
            }
        }
        if (confidence != null && confidence >= 0.85) {
            return PriorityEnum.P0;
        }
        return PriorityEnum.P1;
    }

    private List<String> safeList(List<String> values) {
        return values == null ? List.of() : values;
    }

    @SafeVarargs
    private final List<String> firstNonEmpty(List<String>... values) {
        for (List<String> value : values) {
            if (value != null && !value.isEmpty()) {
                return value;
            }
        }
        return List.of();
    }
}
