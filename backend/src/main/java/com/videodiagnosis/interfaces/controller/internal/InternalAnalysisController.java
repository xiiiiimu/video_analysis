package com.videodiagnosis.interfaces.controller.internal;

import com.videodiagnosis.application.service.InternalAnalysisFacadeService;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.interfaces.request.InternalAgentResultRequest;
import com.videodiagnosis.interfaces.request.InternalAgentProgressRequest;
import com.videodiagnosis.interfaces.request.InternalDiagnosisResultRequest;
import com.videodiagnosis.interfaces.request.InternalHypothesisRequest;
import com.videodiagnosis.interfaces.response.InternalJobContextResponse;
import com.videodiagnosis.interfaces.response.InternalJobEvidenceResponse;
import com.videodiagnosis.interfaces.response.InternalAgentTraceResponse;
import com.videodiagnosis.interfaces.response.InternalDiagnosisResultResponse;
import com.videodiagnosis.types.common.Result;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 仅供 agent-service 调用的内部 HTTP 接口。
 * Controller 只做参数校验与转发，业务逻辑复用 application 层。
 */
@RestController
@RequestMapping("/internal/v1/analysis")
public class InternalAnalysisController {

    private final InternalAnalysisFacadeService internalAnalysisFacadeService;

    public InternalAnalysisController(InternalAnalysisFacadeService internalAnalysisFacadeService) {
        this.internalAnalysisFacadeService = internalAnalysisFacadeService;
    }

    @GetMapping("/jobs/{jobId}/context")
    public Result<InternalJobContextResponse> getJobContext(@PathVariable String jobId) {
        return Result.ok(internalAnalysisFacadeService.getJobContext(jobId));
    }

    @GetMapping("/jobs/{jobId}/evidence")
    public Result<InternalJobEvidenceResponse> getJobEvidence(@PathVariable String jobId) {
        return Result.ok(internalAnalysisFacadeService.getJobEvidence(jobId));
    }

    @GetMapping("/jobs/{jobId}/agent-runs/{agentRunId}/trace")
    public Result<InternalAgentTraceResponse> getAgentTrace(@PathVariable String jobId,
                                                            @PathVariable String agentRunId) {
        return Result.ok(internalAnalysisFacadeService.getAgentTrace(jobId, agentRunId));
    }

    @PostMapping("/jobs/{jobId}/hypotheses")
    public Result<String> saveHypothesis(@PathVariable String jobId,
                                         @Valid @RequestBody InternalHypothesisRequest body) {
        Finding finding = internalAnalysisFacadeService.saveHypothesis(body);
        return Result.ok(finding.getId());
    }

    /**
     * 一次性保存整次 AgentRun 的结论 + 合成结果（事务写入，按 idempotencyKey 去重）。
     */
    @PostMapping("/jobs/{jobId}/diagnosis-results")
    public Result<InternalDiagnosisResultResponse> saveDiagnosisResult(@PathVariable String jobId,
                                                                       @Valid @RequestBody InternalDiagnosisResultRequest body) {
        return Result.ok(internalAnalysisFacadeService.saveDiagnosisResult(jobId, body));
    }

    @PostMapping("/jobs/{jobId}/agent-results")
    public Result<String> saveAgentResult(@PathVariable String jobId,
                                          @Valid @RequestBody InternalAgentResultRequest body) {
        AnalysisJob job = internalAnalysisFacadeService.handleAgentResult(
                jobId,
                body.status(),
                body.agentRunId(),
                body.resultVersion(),
                body.draftObservations(),
                body.agentTrace(),
                body.errorMessage()
        );
        return Result.ok(job.getId());
    }

    @PostMapping("/jobs/{jobId}/agent-progress")
    public Result<String> updateAgentProgress(@PathVariable String jobId,
                                              @Valid @RequestBody InternalAgentProgressRequest body) {
        internalAnalysisFacadeService.updateAgentProgress(
                jobId,
                body.agentRunId(),
                body.stage(),
                body.percent(),
                body.status(),
                body.shortSummary()
        );
        return Result.ok(jobId);
    }
}
