package com.videodiagnosis.interfaces.response;

import java.time.LocalDateTime;
import java.util.List;

public record VideoFeatureResponse(
        String videoId,
        String featureId,
        String featureVersion,
        int keyframeCount,
        List<String> keyframes,
        String sceneJson,
        String ocrJson,
        String transcriptText,
        int transcriptLength,
        String status,
        LocalDateTime createdAt
) {
}
