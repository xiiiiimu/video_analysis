package com.videodiagnosis.interfaces.response;

import java.util.List;

public record InternalVideoEvidenceResponse(
        String videoAssetId,
        String transcriptText,
        List<String> keyframes,
        String sceneJson,
        String ocrJson,
        String timelineJson
) {
}
