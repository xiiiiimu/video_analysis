package com.videodiagnosis.interfaces.response;

public record UploadVideoResponse(
        String videoId,
        String objectName,
        String fileUrl,
        String title,
        String status
) {
}