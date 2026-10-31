package com.videodiagnosis.domain.valueobject;

public record VideoMeta(long durationMs, int width, int height, long bitrate, String mimeType) {
}
