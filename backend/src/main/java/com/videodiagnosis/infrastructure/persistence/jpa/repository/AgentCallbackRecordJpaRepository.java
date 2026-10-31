package com.videodiagnosis.infrastructure.persistence.jpa.repository;

import com.videodiagnosis.infrastructure.persistence.jpa.entity.AgentCallbackRecordJpaEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AgentCallbackRecordJpaRepository extends JpaRepository<AgentCallbackRecordJpaEntity, String> {

    boolean existsByAgentRunIdAndResultVersion(String agentRunId, Integer resultVersion);
}
