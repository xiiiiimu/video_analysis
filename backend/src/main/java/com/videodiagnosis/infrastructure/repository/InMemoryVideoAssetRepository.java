package com.videodiagnosis.infrastructure.repository;

import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.repository.VideoAssetRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class InMemoryVideoAssetRepository implements VideoAssetRepository {

    private final Map<String, VideoAsset> store = new ConcurrentHashMap<>();

    @Override
    public VideoAsset save(VideoAsset asset) {
        if (asset.getId() == null) {
            asset.setId(UUID.randomUUID().toString());
        }
        store.put(asset.getId(), asset);
        return asset;
    }

    @Override
    public Optional<VideoAsset> findById(String id) {
        return Optional.ofNullable(store.get(id));
    }

    @Override
    public List<VideoAsset> findAllByIds(List<String> ids) {
        return ids.stream().map(store::get).filter(java.util.Objects::nonNull).toList();
    }
}
