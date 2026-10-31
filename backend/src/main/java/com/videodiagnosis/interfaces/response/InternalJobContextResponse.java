package com.videodiagnosis.interfaces.response;

import java.util.List;

public record InternalJobContextResponse(
        String jobId,
        String status,
        String currentStage,
        Integer progress,
        String targetVideoId,
        List<String> referenceVideoIds,
        String inputSnapshotJson
) {
}
