package com.videodiagnosis.infrastructure.persistence.repository;

import com.videodiagnosis.infrastructure.persistence.jpa.entity.DiagnosisResultRecordJpaEntity;
import com.videodiagnosis.infrastructure.persistence.jpa.repository.DiagnosisResultRecordJpaRepository;
import com.videodiagnosis.infrastructure.persistence.mapper.PersistenceMapper;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * agent-service 结论保存的幂等记录（与 AgentCallbackRecordRepository 同样的用法：application 层直接使用）。
 */
@Repository
public class DiagnosisResultRecordRepository {

    private final DiagnosisResultRecordJpaRepository repository;
    private final PersistenceMapper persistenceMapper;

    public DiagnosisResultRecordRepository(DiagnosisResultRecordJpaRepository repository,
                                           PersistenceMapper persistenceMapper) {
        this.repository = repository;
        this.persistenceMapper = persistenceMapper;
    }

    public Optional<StoredResult> findByIdempotencyKey(String idempotencyKey) {
        if (idempotencyKey == null || idempotencyKey.isBlank()) {
            return Optional.empty();
        }
        return repository.findByIdempotencyKey(idempotencyKey).map(this::toStored);
    }

    public void save(String jobId,
                     String agentRunId,
                     Integer resultVersion,
                     String idempotencyKey,
                     List<String> findingIds,
                     String synthesisJson) {
        DiagnosisResultRecordJpaEntity entity = new DiagnosisResultRecordJpaEntity();
        entity.setId(UUID.randomUUID().toString());
        entity.setJobId(jobId);
        entity.setAgentRunId(agentRunId);
        entity.setResultVersion(resultVersion);
        entity.setIdempotencyKey(idempotencyKey);
        entity.setFindingIdsJson(persistenceMapper.writeList(findingIds));
        entity.setSynthesisJson(synthesisJson);
        entity.setCreatedAt(LocalDateTime.now());
        repository.save(entity);
    }

    public Optional<String> findLatestSynthesisJson(String jobId) {
        return repository.findFirstByJobIdAndSynthesisJsonIsNotNullOrderByCreatedAtDesc(jobId)
                .map(DiagnosisResultRecordJpaEntity::getSynthesisJson);
    }

    private StoredResult toStored(DiagnosisResultRecordJpaEntity entity) {
        return new StoredResult(entity.getJobId(), persistenceMapper.readList(entity.getFindingIdsJson()));
    }

    public record StoredResult(String jobId, List<String> findingIds) {
    }
}
