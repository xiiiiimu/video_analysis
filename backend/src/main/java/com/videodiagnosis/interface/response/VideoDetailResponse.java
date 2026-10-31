package com.videodiagnosis.interfaces.response;

public record VideoDetailResponse(
        String videoId,
        String role,
        String title,
        String description,
        String status,
        String fileUrl,
        String coverUrl,
        long durationMs,
        String mimeType
) {
}

