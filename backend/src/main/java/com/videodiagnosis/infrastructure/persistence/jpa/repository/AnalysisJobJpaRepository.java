package com.videodiagnosis.infrastructure.persistence.jpa.repository;

import com.videodiagnosis.infrastructure.persistence.jpa.entity.AnalysisJobJpaEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface AnalysisJobJpaRepository extends JpaRepository<AnalysisJobJpaEntity, String> {
    Optional<AnalysisJobJpaEntity> findByJobKey(String jobKey);

    List<AnalysisJobJpaEntity> findByStatusAndUpdatedAtBefore(String status, LocalDateTime threshold);

    @Query("""
            select j from AnalysisJobJpaEntity j
            where j.status in ('WAITING_AGENT', 'RETRYING')
              and (j.nextRetryAt is null or j.nextRetryAt <= :now)
            order by j.updatedAt asc
            """)
    List<AnalysisJobJpaEntity> findDispatchable(@Param("now") LocalDateTime now);

    @Query("""
            select j from AnalysisJobJpaEntity j
            where j.status = 'AGENT_RUNNING'
              and j.agentTimeoutAt is not null
              and j.agentTimeoutAt <= :now
            order by j.agentTimeoutAt asc
            """)
    List<AnalysisJobJpaEntity> findTimedOutAgentJobs(@Param("now") LocalDateTime now);
}
