package com.videodiagnosis.application.view;

import java.time.LocalDateTime;

public record AnalysisProgressSnapshot(
        String jobId,
        String status,
        int progress,
        String stage,
        LocalDateTime updatedAt,
        String agentRunId,
        String shortSummary
) {
    public AnalysisProgressSnapshot(String jobId,
                                    String status,
                                    int progress,
                                    String stage,
                                    LocalDateTime updatedAt) {
        this(jobId, status, progress, stage, updatedAt, null, null);
    }
}
