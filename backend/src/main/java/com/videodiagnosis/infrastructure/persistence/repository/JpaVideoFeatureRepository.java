package com.videodiagnosis.infrastructure.persistence.repository;

import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.repository.VideoFeatureRepository;
import com.videodiagnosis.infrastructure.persistence.jpa.repository.VideoFeatureJpaRepository;
import com.videodiagnosis.infrastructure.persistence.mapper.PersistenceConverter;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@Primary
public class JpaVideoFeatureRepository implements VideoFeatureRepository {

    private final VideoFeatureJpaRepository repository;
    private final PersistenceConverter converter;

    public JpaVideoFeatureRepository(VideoFeatureJpaRepository repository, PersistenceConverter converter) {
        this.repository = repository;
        this.converter = converter;
    }

    @Override
    public VideoFeature save(VideoFeature feature) {
        repository.save(converter.toEntity(feature));
        return feature;
    }

    @Override
    public Optional<VideoFeature> findByVideoAssetId(String videoAssetId) {
        return repository.findByVideoAssetId(videoAssetId).map(converter::toDomain);
    }

    @Override
    public List<VideoFeature> findByJobId(String jobId) {
        return repository.findByJobId(jobId).stream().map(converter::toDomain).toList();
    }
}