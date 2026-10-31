package com.videodiagnosis.infrastructure.repository;

import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.repository.VideoFeatureRepository;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class InMemoryVideoFeatureRepository implements VideoFeatureRepository {

    private final Map<String, VideoFeature> byId = new ConcurrentHashMap<>();
    private final Map<String, VideoFeature> byVideoAssetId = new ConcurrentHashMap<>();
    private final Map<String, List<VideoFeature>> byJobId = new ConcurrentHashMap<>();

    @Override
    public VideoFeature save(VideoFeature feature) {
        if (feature.getId() == null) {
            feature.setId(UUID.randomUUID().toString());
        }
        byId.put(feature.getId(), feature);
        byVideoAssetId.put(feature.getVideoAssetId(), feature);
        byJobId.computeIfAbsent(feature.getJobId(), key -> new ArrayList<>()).removeIf(item -> item.getId().equals(feature.getId()));
        byJobId.computeIfAbsent(feature.getJobId(), key -> new ArrayList<>()).add(feature);
        return feature;
    }

    @Override
    public Optional<VideoFeature> findByVideoAssetId(String videoAssetId) {
        return Optional.ofNullable(byVideoAssetId.get(videoAssetId));
    }

    @Override
    public List<VideoFeature> findByJobId(String jobId) {
        return List.copyOf(byJobId.getOrDefault(jobId, List.of()));
    }
}
