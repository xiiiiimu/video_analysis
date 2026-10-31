package com.videodiagnosis.application.usecase;

import com.videodiagnosis.application.workflow.AnalysisJobWorkflow;
import org.springframework.stereotype.Component;

/**
 * @deprecated 业务已迁移至 agent-service 异步链路（{@link StartAgentDiagnosisCase} +
 * {@link com.videodiagnosis.infrastructure.client.AgentServiceHttpClient}）。
 * 本类为历史同步入口，仅保留用于比对参考，新业务请勿调用。
 */
@Deprecated
@Component
public class ExecuteDiagnosisCase {

    private final AnalysisJobWorkflow analysisJobWorkflow;

    public ExecuteDiagnosisCase(AnalysisJobWorkflow analysisJobWorkflow) {
        this.analysisJobWorkflow = analysisJobWorkflow;
    }

    public void execute(String jobId) {
        analysisJobWorkflow.execute(jobId);
    }
}
