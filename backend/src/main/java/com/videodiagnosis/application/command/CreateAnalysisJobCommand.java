package com.videodiagnosis.application.command;

import java.util.List;

public record CreateAnalysisJobCommand(
        String targetVideoId,
        List<String> referenceVideoIds,
        String targetTitle,
        String targetDescription,
        List<String> referenceTitles,
        List<String> referenceDescriptions,
        boolean enableCoverAnalysis,
        boolean enablePerformanceAnalysis,
        String criteriaText,
        boolean supplementaryAnalysis,
        String category
) {
}
