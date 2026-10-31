package com.videodiagnosis.infrastructure.persistence.repository;

import com.videodiagnosis.infrastructure.persistence.jpa.entity.AgentCallbackRecordJpaEntity;
import com.videodiagnosis.infrastructure.persistence.jpa.repository.AgentCallbackRecordJpaRepository;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.UUID;

@Repository
public class AgentCallbackRecordRepository {

    private final AgentCallbackRecordJpaRepository repository;

    public AgentCallbackRecordRepository(AgentCallbackRecordJpaRepository repository) {
        this.repository = repository;
    }

    public boolean exists(String agentRunId, int resultVersion) {
        return repository.existsByAgentRunIdAndResultVersion(agentRunId, resultVersion);
    }

    public boolean markProcessed(String jobId, String agentRunId, int resultVersion) {
        AgentCallbackRecordJpaEntity entity = new AgentCallbackRecordJpaEntity();
        entity.setId(UUID.randomUUID().toString());
        entity.setJobId(jobId);
        entity.setAgentRunId(agentRunId);
        entity.setResultVersion(resultVersion);
        entity.setProcessedAt(LocalDateTime.now());
        try {
            repository.save(entity);
            return true;
        } catch (DataIntegrityViolationException ex) {
            return false;
        }
    }
}
