package com.videodiagnosis.application.usecase;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.infrastructure.client.AgentServiceHttpClient;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import com.videodiagnosis.types.enums.JobStatusEnum;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * 启动 Agent 异步诊断：任务置 RUNNING 落库后，HTTP 提交 agent-service，立即返回。
 */
@Component
public class StartAgentDiagnosisCase {

    private static final Logger log = LoggerFactory.getLogger(StartAgentDiagnosisCase.class);

    private final AnalysisJobRepository analysisJobRepository;
    private final AgentServiceHttpClient agentServiceHttpClient;

    public StartAgentDiagnosisCase(AnalysisJobRepository analysisJobRepository,
                                   AgentServiceHttpClient agentServiceHttpClient) {
        this.analysisJobRepository = analysisJobRepository;
        this.agentServiceHttpClient = agentServiceHttpClient;
    }

    public void execute(String jobId) {
        AnalysisJob job = analysisJobRepository.findById(jobId)
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.JOB_NOT_FOUND, "Analysis job not found: " + jobId));

        job.markRunning();
        analysisJobRepository.save(job);

        agentServiceHttpClient.submitJobAsync(jobId, ex -> handleDispatchFailure(jobId, ex));
    }

    private void handleDispatchFailure(String jobId, Exception ex) {
        if (ex == null) {
            return;
        }
        AnalysisJob job = analysisJobRepository.findById(jobId).orElse(null);
        if (job == null || job.getStatus() != JobStatusEnum.RUNNING) {
            return;
        }
        log.error("Agent dispatch failed, marking job {} as FAILED", jobId, ex);
        job.markFailed(ErrorCode.MODEL_FAILED.getCode(), "Failed to dispatch agent job: " + ex.getMessage());
        analysisJobRepository.save(job);
    }
}
