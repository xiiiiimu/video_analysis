package com.videodiagnosis.infrastructure.persistence.jpa.repository;

import com.videodiagnosis.infrastructure.persistence.jpa.entity.FindingJpaEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface FindingJpaRepository extends JpaRepository<FindingJpaEntity, String> {
    List<FindingJpaEntity> findByJobId(String jobId);
}