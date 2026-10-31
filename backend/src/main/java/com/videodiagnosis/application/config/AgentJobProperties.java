package com.videodiagnosis.application.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

@ConfigurationProperties(prefix = "app.agent-job")
public class AgentJobProperties {

    private int maxRetryCount = 3;
    private Duration agentTimeout = Duration.ofMinutes(30);
    private Duration dispatchScanInterval = Duration.ofSeconds(5);
    private Duration timeoutScanInterval = Duration.ofSeconds(30);
    private int dispatchBatchSize = 20;
    private Duration retryBackoffFirst = Duration.ofSeconds(10);
    private Duration retryBackoffSecond = Duration.ofSeconds(30);
    private Duration retryBackoffThird = Duration.ofSeconds(60);

    public int getMaxRetryCount() { return maxRetryCount; }
    public void setMaxRetryCount(int maxRetryCount) { this.maxRetryCount = maxRetryCount; }
    public Duration getAgentTimeout() { return agentTimeout; }
    public void setAgentTimeout(Duration agentTimeout) { this.agentTimeout = agentTimeout; }
    public Duration getDispatchScanInterval() { return dispatchScanInterval; }
    public void setDispatchScanInterval(Duration dispatchScanInterval) { this.dispatchScanInterval = dispatchScanInterval; }
    public Duration getTimeoutScanInterval() { return timeoutScanInterval; }
    public void setTimeoutScanInterval(Duration timeoutScanInterval) { this.timeoutScanInterval = timeoutScanInterval; }
    public int getDispatchBatchSize() { return dispatchBatchSize; }
    public void setDispatchBatchSize(int dispatchBatchSize) { this.dispatchBatchSize = dispatchBatchSize; }
    public Duration getRetryBackoffFirst() { return retryBackoffFirst; }
    public void setRetryBackoffFirst(Duration retryBackoffFirst) { this.retryBackoffFirst = retryBackoffFirst; }
    public Duration getRetryBackoffSecond() { return retryBackoffSecond; }
    public void setRetryBackoffSecond(Duration retryBackoffSecond) { this.retryBackoffSecond = retryBackoffSecond; }
    public Duration getRetryBackoffThird() { return retryBackoffThird; }
    public void setRetryBackoffThird(Duration retryBackoffThird) { this.retryBackoffThird = retryBackoffThird; }
}
