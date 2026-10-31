package com.videodiagnosis.application.view;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.CoverageState;
import com.videodiagnosis.domain.entity.Finding;

import java.util.List;

public record AnalysisResultView(
        AnalysisJob job,
        List<String> coreDimensions,
        List<Finding> findings,
        List<CoverageState> coverageStates,
        List<String> missingInputs,
        List<String> revisionPlan
) {
}
