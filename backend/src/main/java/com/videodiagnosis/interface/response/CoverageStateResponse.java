package com.videodiagnosis.interfaces.response;

public record CoverageStateResponse(
        String dimension,
        String state,
        String reason
) {
}

