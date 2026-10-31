package com.videodiagnosis.application.service;

import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.repository.VideoFeatureRepository;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.springframework.stereotype.Service;

@Service
public class VideoFeatureQueryService {

    private final VideoFeatureRepository videoFeatureRepository;

    public VideoFeatureQueryService(VideoFeatureRepository videoFeatureRepository) {
        this.videoFeatureRepository = videoFeatureRepository;
    }

    public VideoFeature getFeature(String videoId) {
        return videoFeatureRepository.findByVideoAssetId(videoId)
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.VIDEO_NOT_FOUND, "Feature not found for video: " + videoId));
    }
}
