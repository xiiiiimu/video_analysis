package com.videodiagnosis.infrastructure.persistence.repository;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.infrastructure.persistence.jpa.repository.AnalysisJobJpaRepository;
import com.videodiagnosis.infrastructure.persistence.mapper.PersistenceConverter;
import com.videodiagnosis.types.enums.JobStatusEnum;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
@Primary
public class JpaAnalysisJobRepository implements AnalysisJobRepository {

    private final AnalysisJobJpaRepository repository;
    private final PersistenceConverter converter;

    public JpaAnalysisJobRepository(AnalysisJobJpaRepository repository, PersistenceConverter converter) {
        this.repository = repository;
        this.converter = converter;
    }

    @Override
    public AnalysisJob save(AnalysisJob job) {
        return converter.toDomain(repository.save(converter.toEntity(job)));
    }

    @Override
    public Optional<AnalysisJob> findById(String id) {
        return repository.findById(id).map(converter::toDomain);
    }

    @Override
    public Optional<AnalysisJob> findByJobKey(String jobKey) {
        return repository.findByJobKey(jobKey).map(converter::toDomain);
    }

    @Override
    public List<AnalysisJob> findByStatusAndUpdatedAtBefore(JobStatusEnum status, LocalDateTime threshold) {
        return repository.findByStatusAndUpdatedAtBefore(status.name(), threshold).stream()
                .map(converter::toDomain)
                .toList();
    }

    @Override
    public List<AnalysisJob> findDispatchableJobs(LocalDateTime now, int limit) {
        return repository.findDispatchable(now).stream()
                .limit(limit)
                .map(converter::toDomain)
                .toList();
    }

    @Override
    public List<AnalysisJob> findTimedOutAgentJobs(LocalDateTime now, int limit) {
        return repository.findTimedOutAgentJobs(now).stream()
                .limit(limit)
                .map(converter::toDomain)
                .toList();
    }
}
