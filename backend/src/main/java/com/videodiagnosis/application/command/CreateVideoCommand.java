package com.videodiagnosis.application.command;

public record CreateVideoCommand(
        String role,
        String fileUrl,
        String title,
        String description,
        String coverUrl
) {
}
