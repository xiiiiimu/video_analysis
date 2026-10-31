package com.videodiagnosis.application.usecase;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.application.service.AnalysisProgressService;
import com.videodiagnosis.infrastructure.persistence.repository.AgentCallbackRecordRepository;
import com.videodiagnosis.infrastructure.redis.RedisIdempotencyRepository;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import com.videodiagnosis.types.enums.JobStatusEnum;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 处理 agent-service 回调结果：成功置 COMPLETED，失败置 FAILED。
 *
 * <p>{@code @Transactional} 放在类上：原来只标在 7 参数的 execute 上，另外两个重载通过 this 调它，
 * 属于同类自调用，从这两个入口进来时根本没有事务。
 *
 * <p>去重分两层：Redis 快速判重 + 回调记录表 (agent_run_id, result_version) 唯一索引兜底。
 * Redis 标记只在事务提交后写（{@link RedisIdempotencyRepository#markProcessedAfterCommit}），
 * 否则数据库回滚后 Redis 已经记成"处理过"，agent-service 重发回调会被当成重复丢掉，结果就丢了。
 */
@Component
@Transactional
public class HandleAgentResultCase {

    private static final Logger log = LoggerFactory.getLogger(HandleAgentResultCase.class);

    private final AnalysisJobRepository analysisJobRepository;
    private final RedisIdempotencyRepository idempotencyRepository;
    private final AgentCallbackRecordRepository callbackRecordRepository;
    private final AnalysisProgressService progressService;
    private final ObjectMapper objectMapper;

    public HandleAgentResultCase(AnalysisJobRepository analysisJobRepository,
                                 RedisIdempotencyRepository idempotencyRepository,
                                 AgentCallbackRecordRepository callbackRecordRepository,
                                 AnalysisProgressService progressService,
                                 ObjectMapper objectMapper) {
        this.analysisJobRepository = analysisJobRepository;
        this.idempotencyRepository = idempotencyRepository;
        this.callbackRecordRepository = callbackRecordRepository;
        this.progressService = progressService;
        this.objectMapper = objectMapper;
    }

    public AnalysisJob execute(String jobId, String status, List<String> draftObservations, String errorMessage) {
        return execute(jobId, status, null, null, draftObservations, errorMessage);
    }

    public AnalysisJob execute(String jobId,
                               String status,
                               String agentRunId,
                               Integer resultVersion,
                               List<String> draftObservations,
                               String errorMessage) {
        return execute(jobId, status, agentRunId, resultVersion, draftObservations, null, errorMessage);
    }

    public AnalysisJob execute(String jobId,
                               String status,
                               String agentRunId,
                               Integer resultVersion,
                               List<String> draftObservations,
                               List<Map<String, Object>> agentTrace,
                               String errorMessage) {
        AnalysisJob job = analysisJobRepository.findById(jobId)
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.JOB_NOT_FOUND, "Analysis job not found: " + jobId));

        String normalizedRunId = normalizeAgentRunId(job, agentRunId);
        int normalizedVersion = resultVersion == null ? nextResultVersion(job) : resultVersion;

        if (idempotencyRepository.alreadyProcessed(normalizedRunId, normalizedVersion)
                || callbackRecordRepository.exists(normalizedRunId, normalizedVersion)) {
            log.info("duplicate agent callback ignored jobId={} agentRunId={} resultVersion={}",
                    jobId, normalizedRunId, normalizedVersion);
            return job;
        }
        if (job.getStatus() == JobStatusEnum.COMPLETED || job.getStatus() == JobStatusEnum.FAILED) {
            idempotencyRepository.markProcessedAfterCommit(normalizedRunId, normalizedVersion);
            log.info("terminal job callback ignored jobId={} status={} agentRunId={}", jobId, job.getStatus(), normalizedRunId);
            return job;
        }
        if (!job.canAcceptAgentResult(agentRunId, resultVersion, LocalDateTime.now()) && agentRunId != null && !agentRunId.isBlank()) {
            log.warn("stale agent callback rejected jobId={} currentAgentRunId={} callbackAgentRunId={}",
                    jobId, job.getCurrentAgentRunId(), agentRunId);
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, "Stale agent callback: " + agentRunId);
        }

        if ("SUCCESS".equalsIgnoreCase(status)) {
            if ((draftObservations != null && !draftObservations.isEmpty()) || (agentTrace != null && !agentTrace.isEmpty())) {
                job.setSkillVersionSnapshotJson(toResultSnapshotJson(draftObservations, agentTrace));
            }
            if (job.getStatus() == JobStatusEnum.AGENT_RUNNING) {
                job.startResultProcessing();
            }
            job.complete(normalizedRunId, normalizedVersion);
            AnalysisJob saved = analysisJobRepository.save(job);
            callbackRecordRepository.markProcessed(saved.getId(), normalizedRunId, normalizedVersion);
            idempotencyRepository.markProcessedAfterCommit(normalizedRunId, normalizedVersion);
            progressService.updateProgress(saved.getId(), "COMPLETED", 100, saved.getStatus().name());
            return saved;
        }

        String message = errorMessage == null || errorMessage.isBlank()
                ? "Agent diagnosis failed"
                : errorMessage;
        job.markFailed(ErrorCode.MODEL_FAILED.getCode(), message);
        AnalysisJob saved = analysisJobRepository.save(job);
        callbackRecordRepository.markProcessed(saved.getId(), normalizedRunId, normalizedVersion);
        idempotencyRepository.markProcessedAfterCommit(normalizedRunId, normalizedVersion);
        progressService.updateProgress(saved.getId(), "FAILED", saved.getProgress(), saved.getStatus().name());
        return saved;
    }

    private String normalizeAgentRunId(AnalysisJob job, String agentRunId) {
        if (agentRunId != null && !agentRunId.isBlank()) {
            return agentRunId;
        }
        if (job.getCurrentAgentRunId() != null && !job.getCurrentAgentRunId().isBlank()) {
            return job.getCurrentAgentRunId();
        }
        return "legacy-" + job.getId();
    }

    private int nextResultVersion(AnalysisJob job) {
        return job.getLastResultVersion() == null ? 1 : job.getLastResultVersion() + 1;
    }

    private String toResultSnapshotJson(List<String> observations, List<Map<String, Object>> agentTrace) {
        try {
            return objectMapper.writeValueAsString(Map.of(
                    "draftObservations", observations == null ? List.of() : observations,
                    "agentTrace", agentTrace == null ? List.of() : agentTrace
            ));
        } catch (JsonProcessingException ex) {
            return toJsonArray(observations == null ? List.of() : observations);
        }
    }

    private String toJsonArray(List<String> values) {
        return values.stream()
                .map(this::escapeJson)
                .map(value -> "\"" + value + "\"")
                .collect(Collectors.joining(",", "[", "]"));
    }

    private String escapeJson(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
