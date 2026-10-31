package com.videodiagnosis.application.view;

import com.videodiagnosis.domain.entity.AnalysisJob;

public record AnalysisJobCreationResult(
        AnalysisJob job,
        boolean created
) {
}
