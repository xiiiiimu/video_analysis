package com.videodiagnosis.application.usecase;

import com.videodiagnosis.application.config.AgentJobProperties;
import com.videodiagnosis.application.service.AnalysisProgressService;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.domain.service.RetryPolicy;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.TraceContext;
import com.videodiagnosis.types.enums.JobStatusEnum;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;

@Component
public class RecoverTimedOutJobCase {

    private static final Logger log = LoggerFactory.getLogger(RecoverTimedOutJobCase.class);

    private final AnalysisJobRepository analysisJobRepository;
    private final RetryPolicy retryPolicy;
    private final AgentJobProperties properties;
    private final AnalysisProgressService progressService;

    public RecoverTimedOutJobCase(AnalysisJobRepository analysisJobRepository,
                                  RetryPolicy retryPolicy,
                                  AgentJobProperties properties,
                                  AnalysisProgressService progressService) {
        this.analysisJobRepository = analysisJobRepository;
        this.retryPolicy = retryPolicy;
        this.properties = properties;
        this.progressService = progressService;
    }

    public int recoverTimedOutJobs() {
        List<AnalysisJob> jobs = analysisJobRepository.findTimedOutAgentJobs(
                LocalDateTime.now(),
                properties.getDispatchBatchSize()
        );
        int recovered = 0;
        for (AnalysisJob job : jobs) {
            if (recoverOne(job.getId())) {
                recovered++;
            }
        }
        return recovered;
    }

    /**
     * 回收一个超时任务。不加 {@code @Transactional}：原注解是同类自调用（recoverTimedOutJobs → recoverOne），本来就不生效；
     * 这里只有一次 save，它自带事务，并发安全靠任务表的 {@code @Version} 乐观锁。
     */
    public boolean recoverOne(String jobId) {
        AnalysisJob job = analysisJobRepository.findById(jobId).orElse(null);
        // 扫描到之后回调可能已经先到（任务已完成 / 失败）：只回收仍在 AGENT_RUNNING 且确实超时的任务。
        // 原来没判断状态，对已完成任务调 retry() 会抛状态机异常，整批扫描在这一条上中断。
        if (job == null
                || job.getStatus() != JobStatusEnum.AGENT_RUNNING
                || job.getAgentTimeoutAt() == null
                || job.getAgentTimeoutAt().isAfter(LocalDateTime.now())) {
            return false;
        }
        try (TraceContext.Scope ignored = TraceContext.open(job.getCurrentAgentRunId(), jobId)) {
            String message = "Agent callback timeout, agentRunId=" + job.getCurrentAgentRunId();
            if (job.canRetry()) {
                job.retry(message, retryPolicy.nextRetryAt(job.getRetryCount() + 1));
                analysisJobRepository.save(job);
                progressService.updateProgress(job.getId(), "RETRYING", job.getProgress(), job.getStatus().name());
                log.warn("agent timeout recovered to retry jobId={} retryCount={}", jobId, job.getRetryCount());
                return true;
            }
            job.markFailed(ErrorCode.MODEL_FAILED.getCode(), message);
            analysisJobRepository.save(job);
            progressService.updateProgress(job.getId(), "FAILED", job.getProgress(), job.getStatus().name());
            log.error("agent timeout failed permanently jobId={}", jobId);
            return true;
        } catch (OptimisticLockingFailureException ex) {
            log.warn("timeout recovery optimistic lock conflict jobId={}", jobId, ex);
            return false;
        }
    }
}
