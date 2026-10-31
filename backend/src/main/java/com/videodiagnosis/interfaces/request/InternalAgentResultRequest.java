package com.videodiagnosis.interfaces.request;

import jakarta.validation.constraints.NotBlank;

import java.util.List;
import java.util.Map;

public record InternalAgentResultRequest(
        @NotBlank String jobId,
        @NotBlank String status,
        String agentRunId,
        Integer resultVersion,
        List<String> draftObservations,
        List<Map<String, Object>> agentTrace,
        String errorMessage
) {
    public InternalAgentResultRequest(String jobId,
                                      String status,
                                      List<String> draftObservations,
                                      String errorMessage) {
        this(jobId, status, null, null, draftObservations, null, errorMessage);
    }

    public InternalAgentResultRequest(String jobId,
                                      String status,
                                      String agentRunId,
                                      Integer resultVersion,
                                      List<String> draftObservations,
                                      String errorMessage) {
        this(jobId, status, agentRunId, resultVersion, draftObservations, null, errorMessage);
    }
}
