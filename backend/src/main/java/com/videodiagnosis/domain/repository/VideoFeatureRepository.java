package com.videodiagnosis.domain.repository;

import com.videodiagnosis.domain.entity.VideoFeature;

import java.util.List;
import java.util.Optional;

public interface VideoFeatureRepository {

    VideoFeature save(VideoFeature feature);

    Optional<VideoFeature> findByVideoAssetId(String videoAssetId);

    List<VideoFeature> findByJobId(String jobId);
}
