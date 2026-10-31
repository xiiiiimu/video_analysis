package com.videodiagnosis.interfaces.response;

public record AnalysisRecommendationResponse(
        String dimension,
        String priority,
        String title,
        String action,
        double confidence
) {
}
