package com.videodiagnosis.domain.repository;

import com.videodiagnosis.domain.entity.VideoAsset;

import java.util.List;
import java.util.Optional;

public interface VideoAssetRepository {

    VideoAsset save(VideoAsset asset);

    Optional<VideoAsset> findById(String id);

    List<VideoAsset> findAllByIds(List<String> ids);
}
