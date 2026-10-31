package com.videodiagnosis.interfaces.response;

public record AnalysisJobDetailResponse(
        String jobId,
        String status,
        int progress,
        String currentStage,
        String errorMessage,
        java.time.LocalDateTime startedAt,
        java.time.LocalDateTime finishedAt
) {
}

