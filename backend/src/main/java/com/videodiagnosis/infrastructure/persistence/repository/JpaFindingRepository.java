package com.videodiagnosis.infrastructure.persistence.repository;

import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.repository.FindingRepository;
import com.videodiagnosis.infrastructure.persistence.jpa.repository.FindingJpaRepository;
import com.videodiagnosis.infrastructure.persistence.mapper.PersistenceConverter;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
@Primary
public class JpaFindingRepository implements FindingRepository {

    private final FindingJpaRepository repository;
    private final PersistenceConverter converter;

    public JpaFindingRepository(FindingJpaRepository repository, PersistenceConverter converter) {
        this.repository = repository;
        this.converter = converter;
    }

    @Override
    public Finding save(Finding finding) {
        repository.save(converter.toEntity(finding));
        return finding;
    }

    @Override
    public List<Finding> saveAll(List<Finding> findings) {
        repository.saveAll(findings.stream().map(converter::toEntity).toList());
        return findings;
    }

    @Override
    public List<Finding> findByJobId(String jobId) {
        return repository.findByJobId(jobId).stream().map(converter::toDomain).toList();
    }
}