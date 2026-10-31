package com.videodiagnosis.infrastructure.persistence.repository;

import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.repository.VideoAssetRepository;
import com.videodiagnosis.infrastructure.persistence.jpa.repository.VideoAssetJpaRepository;
import com.videodiagnosis.infrastructure.persistence.mapper.PersistenceConverter;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@Primary
public class JpaVideoAssetRepository implements VideoAssetRepository {

    private final VideoAssetJpaRepository repository;
    private final PersistenceConverter converter;

    public JpaVideoAssetRepository(VideoAssetJpaRepository repository, PersistenceConverter converter) {
        this.repository = repository;
        this.converter = converter;
    }

    @Override
    public VideoAsset save(VideoAsset asset) {
        repository.save(converter.toEntity(asset));
        return asset;
    }

    @Override
    public Optional<VideoAsset> findById(String id) {
        return repository.findById(id).map(converter::toDomain);
    }

    @Override
    public List<VideoAsset> findAllByIds(List<String> ids) {
        return repository.findAllById(ids).stream().map(converter::toDomain).toList();
    }
}