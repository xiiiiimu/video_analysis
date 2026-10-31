package com.videodiagnosis.infrastructure.persistence.repository;

import com.videodiagnosis.domain.entity.CoverageState;
import com.videodiagnosis.domain.repository.CoverageStateRepository;
import com.videodiagnosis.infrastructure.persistence.jpa.repository.CoverageStateJpaRepository;
import com.videodiagnosis.infrastructure.persistence.mapper.PersistenceConverter;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
@Primary
public class JpaCoverageStateRepository implements CoverageStateRepository {

    private final CoverageStateJpaRepository repository;
    private final PersistenceConverter converter;

    public JpaCoverageStateRepository(CoverageStateJpaRepository repository, PersistenceConverter converter) {
        this.repository = repository;
        this.converter = converter;
    }

    @Override
    public CoverageState save(CoverageState coverageState) {
        repository.save(converter.toEntity(coverageState));
        return coverageState;
    }

    @Override
    public List<CoverageState> saveAll(List<CoverageState> coverageStates) {
        repository.saveAll(coverageStates.stream().map(converter::toEntity).toList());
        return coverageStates;
    }

    @Override
    public List<CoverageState> findByJobId(String jobId) {
        return repository.findByJobId(jobId).stream().map(converter::toDomain).toList();
    }
}