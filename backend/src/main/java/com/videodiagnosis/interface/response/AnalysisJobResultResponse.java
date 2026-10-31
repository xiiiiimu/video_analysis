package com.videodiagnosis.interfaces.response;

import java.util.List;

public record AnalysisJobResultResponse(
        String jobId,
        String status,
        List<String> coreDimensions,
        List<FindingResponse> summary,
        List<AnalysisRecommendationResponse> recommendations,
        List<CoverageStateResponse> coverageStates,
        List<String> missingInputs,
        List<String> revisionPlan
) {
}

