package com.videodiagnosis.domain.repository;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.types.enums.JobStatusEnum;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface AnalysisJobRepository {

    AnalysisJob save(AnalysisJob job);

    Optional<AnalysisJob> findById(String id);

    Optional<AnalysisJob> findByJobKey(String jobKey);

    List<AnalysisJob> findByStatusAndUpdatedAtBefore(JobStatusEnum status, LocalDateTime threshold);

    List<AnalysisJob> findDispatchableJobs(LocalDateTime now, int limit);

    List<AnalysisJob> findTimedOutAgentJobs(LocalDateTime now, int limit);
}
