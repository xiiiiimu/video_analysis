package com.videodiagnosis.application.service;

import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.repository.VideoAssetRepository;
import com.videodiagnosis.domain.repository.VideoFeatureRepository;
import com.videodiagnosis.infrastructure.media.VideoFeatureExtractor;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class VideoFeatureCommandService {

    private static final String AUTO_FRAME_JOB_ID = "AUTO_FRAME";

    private final VideoAssetRepository videoAssetRepository;
    private final VideoFeatureRepository videoFeatureRepository;
    private final VideoFeatureExtractor videoFeatureExtractor;

    public VideoFeatureCommandService(VideoAssetRepository videoAssetRepository,
                                      VideoFeatureRepository videoFeatureRepository,
                                      VideoFeatureExtractor videoFeatureExtractor) {
        this.videoAssetRepository = videoAssetRepository;
        this.videoFeatureRepository = videoFeatureRepository;
        this.videoFeatureExtractor = videoFeatureExtractor;
    }

    public VideoFeature extractAndStoreKeyframes(String videoId) {
        VideoFeature existingFeature = videoFeatureRepository.findByVideoAssetId(videoId).orElse(null);
        // 旧版本（0.1.0，只覆盖前 15 秒、没有转写）提取的特征需要重新提取
        if (existingFeature != null && VideoFeatureExtractor.FEATURE_VERSION.equals(existingFeature.getFeatureVersion())) {
            return existingFeature;
        }

        VideoAsset asset = videoAssetRepository.findById(videoId)
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.VIDEO_NOT_FOUND, "Video not found: " + videoId));

        asset.markProcessing();
        videoAssetRepository.save(asset);

        try {
            VideoFeature feature = new VideoFeature();
            feature.setId(existingFeature != null ? existingFeature.getId() : UUID.randomUUID().toString());
            feature.setVideoAssetId(asset.getId());
            feature.setJobId(AUTO_FRAME_JOB_ID);
            videoFeatureExtractor.extractInto(feature, asset);
            feature.setCreatedAt(LocalDateTime.now());
            feature.setUpdatedAt(LocalDateTime.now());
            videoFeatureRepository.save(feature);

            asset.markProcessed();
            videoAssetRepository.save(asset);
            return feature;
        } catch (RuntimeException ex) {
            asset.markFailed();
            videoAssetRepository.save(asset);
            throw ex;
        }
    }
}
