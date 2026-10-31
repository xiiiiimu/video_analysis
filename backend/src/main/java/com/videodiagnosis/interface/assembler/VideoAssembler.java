package com.videodiagnosis.interfaces.assembler;

import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.interfaces.response.VideoFeatureResponse;
import com.videodiagnosis.interfaces.response.VideoDetailResponse;

public class VideoAssembler {

    public VideoDetailResponse toDetailResponse(VideoAsset asset) {
        return new VideoDetailResponse(
                asset.getId(),
                asset.getRole(),
                asset.getTitle(),
                asset.getDescription(),
                String.valueOf(asset.getStatus()),
                asset.getFileUrl(),
                asset.getCoverUrl(),
                asset.getDurationMs(),
                asset.getMimeType()
        );
    }

    public VideoFeatureResponse toFeatureResponse(VideoFeature feature) {
        return new VideoFeatureResponse(
                feature.getVideoAssetId(),
                feature.getId(),
                feature.getFeatureVersion(),
                feature.getKeyframes() == null ? 0 : feature.getKeyframes().size(),
                feature.getKeyframes(),
                feature.getSceneJson(),
                feature.getOcrJson(),
                feature.getTranscriptText(),
                feature.getTranscriptText() == null ? 0 : feature.getTranscriptText().length(),
                "EXTRACTED",
                feature.getCreatedAt()
        );
    }
}

