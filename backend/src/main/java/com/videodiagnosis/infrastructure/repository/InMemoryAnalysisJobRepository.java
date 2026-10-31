package com.videodiagnosis.infrastructure.repository;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.types.enums.JobStatusEnum;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class InMemoryAnalysisJobRepository implements AnalysisJobRepository {

    private final Map<String, AnalysisJob> byId = new ConcurrentHashMap<>();
    private final Map<String, AnalysisJob> byJobKey = new ConcurrentHashMap<>();

    @Override
    public AnalysisJob save(AnalysisJob job) {
        byId.put(job.getId(), job);
        if (job.getJobKey() != null) {
            byJobKey.put(job.getJobKey(), job);
        }
        return job;
    }

    @Override
    public Optional<AnalysisJob> findById(String id) {
        return Optional.ofNullable(byId.get(id));
    }

    @Override
    public Optional<AnalysisJob> findByJobKey(String jobKey) {
        return Optional.ofNullable(byJobKey.get(jobKey));
    }

    @Override
    public List<AnalysisJob> findByStatusAndUpdatedAtBefore(JobStatusEnum status, LocalDateTime threshold) {
        return byId.values().stream()
                .filter(job -> job.getStatus() == status)
                .filter(job -> job.getUpdatedAt() != null && job.getUpdatedAt().isBefore(threshold))
                .toList();
    }

    @Override
    public List<AnalysisJob> findDispatchableJobs(LocalDateTime now, int limit) {
        return byId.values().stream()
                .filter(job -> job.getStatus() == JobStatusEnum.WAITING_AGENT || job.getStatus() == JobStatusEnum.RETRYING)
                .filter(job -> job.getNextRetryAt() == null || !job.getNextRetryAt().isAfter(now))
                .limit(limit)
                .toList();
    }

    @Override
    public List<AnalysisJob> findTimedOutAgentJobs(LocalDateTime now, int limit) {
        return byId.values().stream()
                .filter(job -> job.getStatus() == JobStatusEnum.AGENT_RUNNING)
                .filter(job -> job.getAgentTimeoutAt() != null && !job.getAgentTimeoutAt().isAfter(now))
                .limit(limit)
                .toList();
    }
}
