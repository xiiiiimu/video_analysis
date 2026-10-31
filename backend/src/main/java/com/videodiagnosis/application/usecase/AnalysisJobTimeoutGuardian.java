package com.videodiagnosis.application.usecase;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.enums.JobStatusEnum;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 扫描长时间 RUNNING 的任务，超时自动置 FAILED。
 */
@Component
public class AnalysisJobTimeoutGuardian {

    private static final Logger log = LoggerFactory.getLogger(AnalysisJobTimeoutGuardian.class);

    private final AnalysisJobRepository analysisJobRepository;
    private final long timeoutMinutes;

    public AnalysisJobTimeoutGuardian(AnalysisJobRepository analysisJobRepository,
                                     @Value("${app.diagnosis.running-timeout-minutes:30}") long timeoutMinutes) {
        this.analysisJobRepository = analysisJobRepository;
        this.timeoutMinutes = timeoutMinutes;
    }

    @Scheduled(fixedDelayString = "${app.diagnosis.timeout-scan-interval-ms:60000}")
    public void scanTimedOutJobs() {
        LocalDateTime threshold = LocalDateTime.now().minusMinutes(timeoutMinutes);
        List<AnalysisJob> staleJobs = analysisJobRepository.findByStatusAndUpdatedAtBefore(JobStatusEnum.RUNNING, threshold);
        for (AnalysisJob job : staleJobs) {
            log.warn("Marking stale RUNNING job as FAILED: {}", job.getId());
            job.markFailed(ErrorCode.MODEL_FAILED.getCode(), "Agent diagnosis timed out after " + timeoutMinutes + " minutes");
            analysisJobRepository.save(job);
        }
    }
}
