package com.videodiagnosis.infrastructure.persistence.jpa.repository;

import com.videodiagnosis.infrastructure.persistence.jpa.entity.DiagnosisResultRecordJpaEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface DiagnosisResultRecordJpaRepository extends JpaRepository<DiagnosisResultRecordJpaEntity, String> {

    Optional<DiagnosisResultRecordJpaEntity> findByIdempotencyKey(String idempotencyKey);

    Optional<DiagnosisResultRecordJpaEntity> findFirstByJobIdAndSynthesisJsonIsNotNullOrderByCreatedAtDesc(String jobId);
}
