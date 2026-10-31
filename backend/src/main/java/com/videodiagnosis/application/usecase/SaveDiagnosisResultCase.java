package com.videodiagnosis.application.usecase;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.repository.FindingRepository;
import com.videodiagnosis.infrastructure.persistence.repository.DiagnosisResultRecordRepository;
import com.videodiagnosis.interfaces.request.InternalDiagnosisResultRequest;
import com.videodiagnosis.interfaces.request.InternalHypothesisRequest;
import com.videodiagnosis.interfaces.response.InternalDiagnosisResultResponse;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

/**
 * 一次性、幂等地保存整次 AgentRun 的结论 + 跨维度合成结果。
 *
 * <ul>
 *     <li>同一事务内写入全部 Finding 与幂等记录：要么全部成功，要么全部不写，不会出现“存了一半”；</li>
 *     <li>同一个 idempotencyKey 重复提交时直接返回第一次的 Finding id（duplicate=true），不会重复写入。</li>
 * </ul>
 */
@Component
public class SaveDiagnosisResultCase {

    private final SaveAgentHypothesisCase saveAgentHypothesisCase;
    private final FindingRepository findingRepository;
    private final DiagnosisResultRecordRepository resultRecordRepository;
    private final ObjectMapper objectMapper;

    public SaveDiagnosisResultCase(SaveAgentHypothesisCase saveAgentHypothesisCase,
                                   FindingRepository findingRepository,
                                   DiagnosisResultRecordRepository resultRecordRepository,
                                   ObjectMapper objectMapper) {
        this.saveAgentHypothesisCase = saveAgentHypothesisCase;
        this.findingRepository = findingRepository;
        this.resultRecordRepository = resultRecordRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public InternalDiagnosisResultResponse execute(String pathJobId, InternalDiagnosisResultRequest request) {
        if (!pathJobId.equals(request.jobId())) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, "jobId in path and body do not match");
        }
        saveAgentHypothesisCase.requireJob(request.jobId());

        Optional<DiagnosisResultRecordRepository.StoredResult> existing =
                resultRecordRepository.findByIdempotencyKey(request.idempotencyKey());
        if (existing.isPresent()) {
            return new InternalDiagnosisResultResponse(request.jobId(), existing.get().findingIds(), true);
        }

        List<Finding> findings = request.findings().stream()
                .map(item -> saveAgentHypothesisCase.toFinding(withJobId(item, request.jobId())))
                .toList();
        findingRepository.saveAll(findings);
        List<String> findingIds = findings.stream().map(Finding::getId).toList();

        resultRecordRepository.save(
                request.jobId(),
                request.agentRunId(),
                request.resultVersion(),
                request.idempotencyKey(),
                findingIds,
                writeSynthesis(request)
        );
        return new InternalDiagnosisResultResponse(request.jobId(), findingIds, false);
    }

    private InternalHypothesisRequest withJobId(InternalHypothesisRequest item, String jobId) {
        if (jobId.equals(item.jobId())) {
            return item;
        }
        return new InternalHypothesisRequest(
                jobId,
                item.dimension(),
                item.observation(),
                item.differenceText(),
                item.hypothesisText(),
                item.suggestedAction(),
                item.evidenceRefs(),
                item.videoEvidenceRefs(),
                item.knowledgeEvidenceRefs(),
                item.targetFrameRefs(),
                item.referenceFrameRefs(),
                item.counterEvidence(),
                item.confidence(),
                item.skillKey(),
                item.outcome(),
                item.findingType(),
                item.idempotencyKey(),
                item.priority()
        );
    }

    private String writeSynthesis(InternalDiagnosisResultRequest request) {
        if (request.synthesis() == null) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(request.synthesis());
        } catch (JsonProcessingException ex) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, "Invalid synthesis payload");
        }
    }
}
