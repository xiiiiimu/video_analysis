package com.videodiagnosis.infrastructure.persistence.jpa.repository;

import com.videodiagnosis.infrastructure.persistence.jpa.entity.VideoFeatureJpaEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface VideoFeatureJpaRepository extends JpaRepository<VideoFeatureJpaEntity, String> {
    Optional<VideoFeatureJpaEntity> findByVideoAssetId(String videoAssetId);
    List<VideoFeatureJpaEntity> findByJobId(String jobId);
}