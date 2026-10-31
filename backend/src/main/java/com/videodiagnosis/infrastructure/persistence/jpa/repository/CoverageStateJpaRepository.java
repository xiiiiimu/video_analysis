package com.videodiagnosis.infrastructure.persistence.jpa.repository;

import com.videodiagnosis.infrastructure.persistence.jpa.entity.CoverageStateJpaEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CoverageStateJpaRepository extends JpaRepository<CoverageStateJpaEntity, String> {
    List<CoverageStateJpaEntity> findByJobId(String jobId);
}