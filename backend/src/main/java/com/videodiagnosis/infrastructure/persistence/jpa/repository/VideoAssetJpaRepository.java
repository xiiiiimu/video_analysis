package com.videodiagnosis.infrastructure.persistence.jpa.repository;

import com.videodiagnosis.infrastructure.persistence.jpa.entity.VideoAssetJpaEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface VideoAssetJpaRepository extends JpaRepository<VideoAssetJpaEntity, String> {
}