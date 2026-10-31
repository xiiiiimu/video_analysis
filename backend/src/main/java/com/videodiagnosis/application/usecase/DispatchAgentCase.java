package com.videodiagnosis.application.usecase;

import com.videodiagnosis.application.config.AgentJobProperties;
import com.videodiagnosis.application.port.AgentDispatchPort;
import com.videodiagnosis.application.service.AnalysisProgressService;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.exception.InvalidJobStateTransitionException;
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
import java.util.UUID;

@Component
public class DispatchAgentCase {

    private static final Logger log = LoggerFactory.getLogger(DispatchAgentCase.class);

    private final AnalysisJobRepository analysisJobRepository;
    private final AgentDispatchPort agentDispatchPort;
    private final RetryPolicy retryPolicy;
    private final AgentJobProperties properties;
    private final AnalysisProgressService progressService;

    public DispatchAgentCase(AnalysisJobRepository analysisJobRepository,
                             AgentDispatchPort agentDispatchPort,
                             RetryPolicy retryPolicy,
                             AgentJobProperties properties,
                             AnalysisProgressService progressService) {
        this.analysisJobRepository = analysisJobRepository;
        this.agentDispatchPort = agentDispatchPort;
        this.retryPolicy = retryPolicy;
        this.properties = properties;
        this.progressService = progressService;
    }

    public int dispatchReadyJobs() {
        List<AnalysisJob> jobs = analysisJobRepository.findDispatchableJobs(
                LocalDateTime.now(),
                properties.getDispatchBatchSize()
        );
        int dispatched = 0;
        for (AnalysisJob job : jobs) {
            if (dispatchOne(job.getId())) {
                dispatched++;
            }
        }
        return dispatched;
    }

    /**
     * 派发一个任务。刻意不加 {@code @Transactional}：
     * <ol>
     *   <li>原来的注解是同类自调用（{@link #dispatchReadyJobs()} → dispatchOne），Spring 代理拦不到，注解根本不生效，只是误导；</li>
     *   <li>真要生效反而更糟：HTTP 调用会被包进事务，agent-service 慢的时候一直占着数据库连接（长事务）。</li>
     * </ol>
     * 现在拆成三步，每步各是一次短事务（repository.save 自带事务，任务表有 {@code @Version} 乐观锁）：
     * 抢占（WAITING_AGENT/RETRYING → AGENT_RUNNING，先提交）→ 事务外发 HTTP → 只有失败才回写 RETRYING / FAILED。
     */
    public boolean dispatchOne(String jobId) {
        String agentRunId = UUID.randomUUID().toString();
        // 一次派发就是一条链路：traceId 直接用 agentRunId，agent-service 的日志和回调都带同一个值
        try (TraceContext.Scope ignored = TraceContext.open(agentRunId, jobId)) {
            AnalysisJob claimed = claim(jobId, agentRunId);
            if (claimed == null) {
                return false;
            }
            progressService.updateProgress(jobId, "AGENT_RUNNING", 60, claimed.getStatus().name());
            try {
                agentDispatchPort.dispatch(jobId, agentRunId);
            } catch (Exception ex) {
                handleDispatchFailure(jobId, agentRunId, ex);
                return false;
            }
            log.info("agent dispatch success jobId={} agentRunId={}", jobId, agentRunId);
            return true;
        }
    }

    /**
     * 抢占：成功返回已提交的任务，没抢到返回 null。
     * 扫描列表是快照，抢占前任务可能已被别的实例抢走（乐观锁冲突）或状态已经变了（状态机拒绝），
     * 这两种都只是"这次不归我"，直接跳过；绝不能当成派发失败去把别人的任务改成 RETRYING。
     */
    private AnalysisJob claim(String jobId, String agentRunId) {
        AnalysisJob job = analysisJobRepository.findById(jobId).orElse(null);
        if (job == null) {
            return null;
        }
        JobStatusEnum before = job.getStatus();
        try {
            job.setMaxRetryCount(retryPolicy.maxRetryCount());
            job.markAgentRunning(agentRunId, LocalDateTime.now().plus(properties.getAgentTimeout()));
            return analysisJobRepository.save(job);
        } catch (InvalidJobStateTransitionException ex) {
            log.info("agent dispatch skipped, job no longer dispatchable jobId={} status={}", jobId, before);
            return null;
        } catch (OptimisticLockingFailureException ex) {
            log.info("agent dispatch skipped, claimed by another worker jobId={}", jobId);
            return null;
        }
    }

    /**
     * 派发失败后回写重试 / 失败。
     * HTTP 失败不代表 agent-service 没收到（例如读超时）：如果回调已经先到、任务已结束，
     * 或者任务已经被超时回收并重新派发（agentRunId 变了），就不再改它。
     */
    private void handleDispatchFailure(String jobId, String agentRunId, Exception ex) {
        AnalysisJob job = analysisJobRepository.findById(jobId).orElse(null);
        if (job == null) {
            return;
        }
        if (job.getStatus() != JobStatusEnum.AGENT_RUNNING || !agentRunId.equals(job.getCurrentAgentRunId())) {
            log.warn("agent dispatch failed but job already moved on, leave it jobId={} status={} currentAgentRunId={}",
                    jobId, job.getStatus(), job.getCurrentAgentRunId(), ex);
            return;
        }
        String message = "Failed to dispatch agent job: " + ex.getMessage();
        try {
            if (job.canRetry()) {
                job.retry(message, retryPolicy.nextRetryAt(job.getRetryCount() + 1));
                analysisJobRepository.save(job);
                progressService.updateProgress(job.getId(), "RETRYING", job.getProgress(), job.getStatus().name());
                log.warn("agent dispatch retry scheduled jobId={} retryCount={} nextRetryAt={}",
                        job.getId(), job.getRetryCount(), job.getNextRetryAt(), ex);
                return;
            }
            job.markFailed(ErrorCode.MODEL_FAILED.getCode(), message);
            analysisJobRepository.save(job);
            progressService.updateProgress(job.getId(), "FAILED", job.getProgress(), job.getStatus().name());
            log.error("agent dispatch failed permanently jobId={}", job.getId(), ex);
        } catch (OptimisticLockingFailureException conflict) {
            // 读到之后回调恰好到达并改了任务：以回调为准
            log.warn("agent dispatch failure not recorded, job changed concurrently jobId={}", jobId);
        }
    }
}
