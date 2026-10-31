package com.videodiagnosis.infrastructure.client;

import com.videodiagnosis.types.common.TraceContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;

@Component
public class AgentServiceHttpClient {

    private static final Logger log = LoggerFactory.getLogger(AgentServiceHttpClient.class);

    private final RestClient restClient;
    private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();

    public AgentServiceHttpClient(AgentServiceProperties properties,
                                  @Value("${app.internal.api-key:change-me-in-production}") String internalApiKey) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(properties.getConnectTimeoutMs());
        requestFactory.setReadTimeout(properties.getReadTimeoutMs());
        this.restClient = RestClient.builder()
                .baseUrl(properties.getBaseUrl())
                .requestFactory(requestFactory)
                // Java -> agent-service 与 agent-service -> Java 使用同一个内部密钥
                .defaultHeader("X-Internal-Api-Key", internalApiKey)
                .build();
    }

    /**
     * 异步提交 Agent 任务，不阻塞调用方。
     */
    public void submitJobAsync(String jobId, Consumer<Exception> onFailure) {
        CompletableFuture.runAsync(() -> {
            try {
                submitJob(jobId);
            } catch (Exception ex) {
                log.error("Async agent submit failed for job {}", jobId, ex);
                if (onFailure != null) {
                    onFailure.accept(ex);
                }
            }
        }, executor);
    }

    public void submitJob(String jobId) {
        submitJob(jobId, null);
    }

    public void submitJob(String jobId, String agentRunId) {
        try {
            Map<String, String> body = agentRunId == null || agentRunId.isBlank()
                    ? Map.of("job_id", jobId)
                    : Map.of("job_id", jobId, "agent_run_id", agentRunId);
            // 派发链路的 traceId 就是 agentRunId；agent-service 用它打日志并在回调时原样带回
            String traceId = agentRunId == null || agentRunId.isBlank() ? TraceContext.currentOrNew() : agentRunId;
            restClient.post()
                    .uri("/api/v1/agent/jobs/submit")
                    .header(TraceContext.HEADER, traceId)
                    .body(body)
                    .retrieve()
                    .toBodilessEntity();
            log.info("Submitted agent job: {}, agentRunId={}", jobId, agentRunId);
        } catch (RestClientException ex) {
            log.error("Failed to submit agent job: {}", jobId, ex);
            throw ex;
        }
    }
}
