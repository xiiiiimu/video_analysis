package com.videodiagnosis.interfaces.response;

public record CreateAnalysisJobResponse(
        String jobId,
        String status
) {
}

