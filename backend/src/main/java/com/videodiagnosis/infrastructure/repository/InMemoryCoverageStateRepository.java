package com.videodiagnosis.infrastructure.repository;

import com.videodiagnosis.domain.entity.CoverageState;
import com.videodiagnosis.domain.repository.CoverageStateRepository;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class InMemoryCoverageStateRepository implements CoverageStateRepository {

    private final Map<String, CoverageState> byId = new ConcurrentHashMap<>();
    private final Map<String, List<CoverageState>> byJobId = new ConcurrentHashMap<>();

    @Override
    public CoverageState save(CoverageState coverageState) {
        if (coverageState.getId() == null) {
            coverageState.setId(UUID.randomUUID().toString());
        }
        byId.put(coverageState.getId(), coverageState);
        byJobId.computeIfAbsent(coverageState.getJobId(), key -> new ArrayList<>()).removeIf(item -> item.getId().equals(coverageState.getId()));
        byJobId.computeIfAbsent(coverageState.getJobId(), key -> new ArrayList<>()).add(coverageState);
        return coverageState;
    }

    @Override
    public List<CoverageState> saveAll(List<CoverageState> coverageStates) {
        return coverageStates.stream().map(this::save).toList();
    }

    @Override
    public List<CoverageState> findByJobId(String jobId) {
        return List.copyOf(byJobId.getOrDefault(jobId, List.of()));
    }
}
