package com.videodiagnosis.infrastructure.scheduler;

import com.videodiagnosis.application.usecase.DispatchAgentCase;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(prefix = "app.agent-job.scheduler", name = "enabled", havingValue = "true", matchIfMissing = true)
public class AgentDispatchScheduler {

    private static final Logger log = LoggerFactory.getLogger(AgentDispatchScheduler.class);

    private final DispatchAgentCase dispatchAgentCase;

    public AgentDispatchScheduler(DispatchAgentCase dispatchAgentCase) {
        this.dispatchAgentCase = dispatchAgentCase;
    }

    @Scheduled(fixedDelayString = "${app.agent-job.dispatch-scan-interval:PT5S}")
    public void scan() {
        int count = dispatchAgentCase.dispatchReadyJobs();
        if (count > 0) {
            log.info("agent dispatch scheduler dispatched jobs={}", count);
        }
    }
}
