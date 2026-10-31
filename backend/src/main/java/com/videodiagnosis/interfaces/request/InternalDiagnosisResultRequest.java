package com.videodiagnosis.interfaces.request;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.util.List;
import java.util.Map;

/**
 * agent-service 一次性提交整次 AgentRun 的结论与跨维度合成结果。
 *
 * <p>同一个 idempotencyKey（agentRunId:v{resultVersion}）重复提交时，返回第一次保存的结果，不会重复写入 Finding。
 */
public record InternalDiagnosisResultRequest(
        @NotBlank String jobId,
        String agentRunId,
        Integer resultVersion,
        @NotBlank String idempotencyKey,
        @NotNull @Valid List<InternalHypothesisRequest> findings,
        Map<String, Object> synthesis
) {
}
