package com.videodiagnosis.application.service;

import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.springframework.stereotype.Service;

@Service
public class VideoAsrQueryService {

    private final VideoFeatureQueryService videoFeatureQueryService;

    public VideoAsrQueryService(VideoFeatureQueryService videoFeatureQueryService) {
        this.videoFeatureQueryService = videoFeatureQueryService;
    }

    public VideoFeature getAsrFeature(String videoId) {
        VideoFeature feature = videoFeatureQueryService.getFeature(videoId);
        if (feature.getTranscriptText() == null || feature.getTranscriptText().isBlank()) {
            throw new VideoDiagnosisException(ErrorCode.VIDEO_NOT_FOUND, "ASR not found for video: " + videoId);
        }
        return feature;
    }
}
