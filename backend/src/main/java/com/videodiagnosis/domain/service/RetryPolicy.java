package com.videodiagnosis.domain.service;

import com.videodiagnosis.application.config.AgentJobProperties;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.time.LocalDateTime;

@Component
public class RetryPolicy {

    private final AgentJobProperties properties;

    public RetryPolicy(AgentJobProperties properties) {
        this.properties = properties;
    }

    public int maxRetryCount() {
        return properties.getMaxRetryCount();
    }

    public LocalDateTime nextRetryAt(int nextRetryCount) {
        return LocalDateTime.now().plus(backoff(nextRetryCount));
    }

    public Duration backoff(int nextRetryCount) {
        if (nextRetryCount <= 1) {
            return properties.getRetryBackoffFirst();
        }
        if (nextRetryCount == 2) {
            return properties.getRetryBackoffSecond();
        }
        return properties.getRetryBackoffThird();
    }
}
