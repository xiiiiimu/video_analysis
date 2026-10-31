package com.videodiagnosis.application.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.application.usecase.GetJobEvidenceCase;
import com.videodiagnosis.application.usecase.HandleAgentResultCase;
import com.videodiagnosis.application.usecase.SaveAgentHypothesisCase;
import com.videodiagnosis.application.usecase.SaveDiagnosisResultCase;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.interfaces.request.InternalDiagnosisResultRequest;
import com.videodiagnosis.interfaces.request.InternalHypothesisRequest;
import com.videodiagnosis.interfaces.response.InternalDiagnosisResultResponse;
import com.videodiagnosis.interfaces.response.InternalJobContextResponse;
import com.videodiagnosis.interfaces.response.InternalJobEvidenceResponse;
import com.videodiagnosis.interfaces.response.InternalAgentTraceResponse;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/**
 * 内部接口门面：只做转发，复用已有 application 用例/服务，不重复业务逻辑。
 */
@Service
public class InternalAnalysisFacadeService {

    private final AnalysisQueryService analysisQueryService;
    private final HandleAgentResultCase handleAgentResultCase;
    private final GetJobEvidenceCase getJobEvidenceCase;
    private final SaveAgentHypothesisCase saveAgentHypothesisCase;
    private final SaveDiagnosisResultCase saveDiagnosisResultCase;
    private final AnalysisProgressService analysisProgressService;
    private final ObjectMapper objectMapper;

    public InternalAnalysisFacadeService(AnalysisQueryService analysisQueryService,
                                         HandleAgentResultCase handleAgentResultCase,
                                         GetJobEvidenceCase getJobEvidenceCase,
                                         SaveAgentHypothesisCase saveAgentHypothesisCase,
                                         SaveDiagnosisResultCase saveDiagnosisResultCase,
                                         AnalysisProgressService analysisProgressService,
                                         ObjectMapper objectMapper) {
        this.analysisQueryService = analysisQueryService;
        this.handleAgentResultCase = handleAgentResultCase;
        this.getJobEvidenceCase = getJobEvidenceCase;
        this.saveAgentHypothesisCase = saveAgentHypothesisCase;
        this.saveDiagnosisResultCase = saveDiagnosisResultCase;
        this.analysisProgressService = analysisProgressService;
        this.objectMapper = objectMapper;
    }

    public InternalJobContextResponse getJobContext(String jobId) {
        AnalysisJob job = analysisQueryService.getJob(jobId);
        return new InternalJobContextResponse(
                job.getId(),
                String.valueOf(job.getStatus()),
                job.getCurrentStage(),
                job.getProgress(),
                job.getTargetVideoId(),
                job.getReferenceVideoIds(),
                job.getInputSnapshotJson()
        );
    }

    public InternalJobEvidenceResponse getJobEvidence(String jobId) {
        return getJobEvidenceCase.execute(jobId);
    }

    public Finding saveHypothesis(InternalHypothesisRequest request) {
        return saveAgentHypothesisCase.execute(request);
    }

    public InternalDiagnosisResultResponse saveDiagnosisResult(String jobId, InternalDiagnosisResultRequest request) {
        return saveDiagnosisResultCase.execute(jobId, request);
    }

    public AnalysisJob handleAgentResult(String jobId, String status, List<String> draftObservations, String errorMessage) {
        return handleAgentResultCase.execute(jobId, status, null, null, draftObservations, errorMessage);
    }

    public AnalysisJob handleAgentResult(String jobId,
                                         String status,
                                         String agentRunId,
                                         Integer resultVersion,
                                         List<String> draftObservations,
                                         String errorMessage) {
        return handleAgentResultCase.execute(jobId, status, agentRunId, resultVersion, draftObservations, null, errorMessage);
    }

    public AnalysisJob handleAgentResult(String jobId,
                                         String status,
                                         String agentRunId,
                                         Integer resultVersion,
                                         List<String> draftObservations,
                                         List<java.util.Map<String, Object>> agentTrace,
                                         String errorMessage) {
        return handleAgentResultCase.execute(jobId, status, agentRunId, resultVersion, draftObservations, agentTrace, errorMessage);
    }

    public void updateAgentProgress(String jobId,
                                    String agentRunId,
                                    String stage,
                                    Integer percent,
                                    String status,
                                    String shortSummary) {
        AnalysisJob job = analysisQueryService.getJob(jobId);
        int safePercent = percent == null ? job.getProgress() : Math.max(job.getProgress(), Math.min(100, percent));
        String safeStatus = status == null || status.isBlank() ? job.getStatus().name() : status;
        analysisProgressService.updateProgress(jobId, stage, safePercent, safeStatus, agentRunId, shortSummary);
    }

    public InternalAgentTraceResponse getAgentTrace(String jobId, String agentRunId) {
        AnalysisJob job = analysisQueryService.getJob(jobId);
        List<Map<String, Object>> steps = readAgentTrace(job.getSkillVersionSnapshotJson(), agentRunId);
        return new InternalAgentTraceResponse(jobId, agentRunId, steps);
    }

    private List<Map<String, Object>> readAgentTrace(String snapshotJson, String agentRunId) {
        if (snapshotJson == null || snapshotJson.isBlank()) {
            return List.of();
        }
        try {
            JsonNode root = objectMapper.readTree(snapshotJson);
            JsonNode traceNode = root.path("agentTrace");
            if (!traceNode.isArray()) {
                return List.of();
            }
            List<Map<String, Object>> rows = objectMapper.convertValue(
                    traceNode,
                    new TypeReference<List<Map<String, Object>>>() {}
            );
            return rows.stream()
                    .filter(row -> agentRunId == null || agentRunId.isBlank() || agentRunId.equals(String.valueOf(row.get("runId"))))
                    .toList();
        } catch (JsonProcessingException | IllegalArgumentException ex) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, "Invalid agent trace snapshot");
        }
    }
}
