package com.videodiagnosis.infrastructure.repository;

import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.repository.FindingRepository;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class InMemoryFindingRepository implements FindingRepository {

    private final Map<String, Finding> byId = new ConcurrentHashMap<>();
    private final Map<String, List<Finding>> byJobId = new ConcurrentHashMap<>();

    @Override
    public Finding save(Finding finding) {
        if (finding.getId() == null) {
            finding.setId(UUID.randomUUID().toString());
        }
        byId.put(finding.getId(), finding);
        byJobId.computeIfAbsent(finding.getJobId(), key -> new ArrayList<>()).removeIf(item -> item.getId().equals(finding.getId()));
        byJobId.computeIfAbsent(finding.getJobId(), key -> new ArrayList<>()).add(finding);
        return finding;
    }

    @Override
    public List<Finding> saveAll(List<Finding> findings) {
        return findings.stream().map(this::save).toList();
    }

    @Override
    public List<Finding> findByJobId(String jobId) {
        return List.copyOf(byJobId.getOrDefault(jobId, List.of()));
    }
}
