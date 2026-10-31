package com.videodiagnosis.interfaces.response;

import java.time.LocalDateTime;

public record VideoAsrResponse(
        String videoId,
        String featureId,
        String transcriptText,
        int transcriptLength,
        int wordCount,
        String status,
        LocalDateTime createdAt
) {
}
