package com.videodiagnosis.interfaces.response;

import java.util.List;

public record FindingResponse(
        String dimension,
        String priority,
        String observation,
        List<String> targetEvidence,
        List<String> referenceEvidence,
        String differenceText,
        String hypothesis,
        double confidence,
        String source,
        String counterEvidence,
        String suggestedAction
) {
}

