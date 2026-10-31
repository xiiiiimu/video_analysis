package com.videodiagnosis.domain.valueobject;

public record TimeRange(long startMs, long endMs) {

    public TimeRange {
        if (endMs < startMs) {
            throw new IllegalArgumentException("endMs must be >= startMs");
        }
    }
}
