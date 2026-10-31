package com.videodiagnosis.interfaces.request;

import jakarta.validation.constraints.NotBlank;

public record CreateVideoRequest(
        @NotBlank String role,
        @NotBlank String fileUrl,
        String title,
        String description,
        String coverUrl
) {
}

