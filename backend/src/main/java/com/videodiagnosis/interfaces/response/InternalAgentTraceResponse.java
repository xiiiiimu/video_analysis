package com.videodiagnosis.interfaces.response;

import java.util.List;
import java.util.Map;

public record InternalAgentTraceResponse(
        String jobId,
        String agentRunId,
        List<Map<String, Object>> steps
) {
}
