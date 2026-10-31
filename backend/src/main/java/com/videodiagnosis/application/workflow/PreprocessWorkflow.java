package com.videodiagnosis.application.workflow;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.repository.VideoAssetRepository;
import com.videodiagnosis.domain.repository.VideoFeatureRepository;
import com.videodiagnosis.infrastructure.media.VideoFeatureExtractor;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import com.videodiagnosis.types.enums.VideoStatusEnum;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Component
public class PreprocessWorkflow {

    private final VideoAssetRepository videoAssetRepository;
    private final VideoFeatureRepository videoFeatureRepository;
    private final VideoFeatureExtractor videoFeatureExtractor;

    public PreprocessWorkflow(VideoAssetRepository videoAssetRepository,
                              VideoFeatureRepository videoFeatureRepository,
                              VideoFeatureExtractor videoFeatureExtractor) {
        this.videoAssetRepository = videoAssetRepository;
        this.videoFeatureRepository = videoFeatureRepository;
        this.videoFeatureExtractor = videoFeatureExtractor;
    }

    public List<VideoFeature> execute(AnalysisJob job) {
        List<VideoFeature> features = new ArrayList<>();
        List<String> allVideoIds = new ArrayList<>();
        allVideoIds.add(job.getTargetVideoId());
        allVideoIds.addAll(job.getReferenceVideoIds());

        for (String videoId : allVideoIds) {
            VideoAsset asset = videoAssetRepository.findById(videoId)
                    .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.VIDEO_NOT_FOUND, "Video not found: " + videoId));
            asset.markProcessing();
            videoAssetRepository.save(asset);

            VideoFeature feature = new VideoFeature();
            feature.setId(UUID.randomUUID().toString());
            feature.setVideoAssetId(asset.getId());
            feature.setJobId(job.getId());
            videoFeatureExtractor.extractInto(feature, asset);
            feature.setCreatedAt(LocalDateTime.now());
            feature.setUpdatedAt(LocalDateTime.now());
            videoFeatureRepository.save(feature);
            asset.setStatus(VideoStatusEnum.PROCESSED);
            videoAssetRepository.save(asset);
            features.add(feature);
        }

        return features;
    }
}
