package com.videodiagnosis.interfaces.request;

import jakarta.validation.constraints.NotBlank;

public record InternalAgentProgressRequest(
        @NotBlank String jobId,
        String agentRunId,
        @NotBlank String stage,
        Integer percent,
        String status,
        String shortSummary
) {
}
