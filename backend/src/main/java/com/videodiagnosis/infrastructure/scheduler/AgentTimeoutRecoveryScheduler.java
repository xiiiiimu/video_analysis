package com.videodiagnosis.infrastructure.scheduler;

import com.videodiagnosis.application.usecase.RecoverTimedOutJobCase;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(prefix = "app.agent-job.scheduler", name = "enabled", havingValue = "true", matchIfMissing = true)
public class AgentTimeoutRecoveryScheduler {

    private static final Logger log = LoggerFactory.getLogger(AgentTimeoutRecoveryScheduler.class);

    private final RecoverTimedOutJobCase recoverTimedOutJobCase;

    public AgentTimeoutRecoveryScheduler(RecoverTimedOutJobCase recoverTimedOutJobCase) {
        this.recoverTimedOutJobCase = recoverTimedOutJobCase;
    }

    @Scheduled(fixedDelayString = "${app.agent-job.timeout-scan-interval:PT30S}")
    public void scan() {
        int count = recoverTimedOutJobCase.recoverTimedOutJobs();
        if (count > 0) {
            log.info("agent timeout scheduler recovered jobs={}", count);
        }
    }
}
