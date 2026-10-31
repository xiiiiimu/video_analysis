package com.videodiagnosis.integration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.application.usecase.StartAgentDiagnosisCase;
import com.videodiagnosis.application.usecase.DispatchAgentCase;
import com.videodiagnosis.application.usecase.RecoverTimedOutJobCase;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.domain.repository.FindingRepository;
import com.videodiagnosis.interfaces.request.InternalAgentResultRequest;
import com.videodiagnosis.types.enums.JobStatusEnum;
import com.videodiagnosis.types.enums.PriorityEnum;
import okhttp3.mockwebserver.Dispatcher;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.QueueDispatcher;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.hamcrest.Matchers.matchesPattern;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Agent 异步链路集成测试骨架。
 *
 * <p>方案：MockWebServer 模拟 agent-service HTTP 提交端点；MockMvc 模拟 agent-service 回调 Java /internal 接口。
 * 不启动真实 agent-service / MySQL / Redis，使用 H2 + test profile。
 *
 * <p>注意：本类为骨架示例，部分用例依赖虚拟线程异步提交，需短暂等待或引入 Awaitility 增强稳定性。
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class AnalysisAgentIntegrationTest {

    private static final String INTERNAL_API_KEY_HEADER = "X-Internal-Api-Key";
    private static final String INTERNAL_API_KEY = "test-internal-api-key";

    private static MockWebServer agentServiceMock;

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private StartAgentDiagnosisCase startAgentDiagnosisCase;

    @Autowired
    private DispatchAgentCase dispatchAgentCase;

    @Autowired
    private RecoverTimedOutJobCase recoverTimedOutJobCase;

    @Autowired
    private AnalysisJobRepository analysisJobRepository;

    @Autowired
    private FindingRepository findingRepository;

    @BeforeAll
    static void startAgentServiceMock() throws IOException {
        agentServiceMock = new MockWebServer();
        agentServiceMock.start();
    }

    @AfterAll
    static void shutdownAgentServiceMock() throws IOException {
        if (agentServiceMock != null) {
            agentServiceMock.shutdown();
        }
    }

    @DynamicPropertySource
    static void overrideAgentServiceBaseUrl(DynamicPropertyRegistry registry) {
        registry.add("app.agent-service.base-url", () -> agentServiceMock.url("/").toString().replaceAll("/$", ""));
    }

    @BeforeEach
    void resetMockServer() {
        // 每个用例前清空 MockWebServer 请求队列，避免串扰。getRequestCount 是累计值，不能作为循环条件。
        try {
            while (agentServiceMock.takeRequest(50, java.util.concurrent.TimeUnit.MILLISECONDS) != null) {
                // drain queued requests
            }
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
        }
    }

    // -------------------------------------------------------------------------
    // 场景 ①：StartAgentDiagnosisCase → 任务状态 RUNNING
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("① 创建任务并触发 StartAgentDiagnosisCase 后，状态应为 RUNNING")
    void shouldMarkJobRunningWhenAgentDispatchAccepted() throws Exception {
        // given: Java 侧已创建 PENDING 任务
        String jobId = seedPendingJob().getId();

        // given: agent-service 接受提交（202 Accepted）
        agentServiceMock.enqueue(new MockResponse().setResponseCode(202).setBody("{\"accepted\":true}"));

        // when: 触发异步 Agent 诊断（不阻塞等待 agent 推理完成）
        startAgentDiagnosisCase.execute(jobId);

        // then: 同步断言 —— 任务应立即进入 RUNNING
        AnalysisJob runningJob = analysisJobRepository.findById(jobId).orElseThrow();
        assertThat(runningJob.getStatus()).isEqualTo(JobStatusEnum.RUNNING);
        assertThat(runningJob.getCurrentStage()).isEqualTo("RUNNING");

        // then: 异步断言 —— Java 应向 agent-service 发起 HTTP 提交
        awaitAgentHttpSubmit();
        // 骨架：可进一步断言 agentServiceMock.takeRequest() 的 path / method / body
        // assertThat(agentServiceMock.takeRequest().getPath()).contains("/api/v1/agent/jobs/submit");
    }

    // -------------------------------------------------------------------------
    // 场景 ②：模拟 agent SUCCESS 回调 → HandleAgentResultCase → COMPLETED
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("② agent 回调 SUCCESS 后，任务应流转为 COMPLETED")
    void shouldCompleteJobWhenAgentCallbackSuccess() throws Exception {
        // given: 任务处于 RUNNING（模拟 agent 正在处理）
        String jobId = seedRunningJob().getId();

        InternalAgentResultRequest callback = new InternalAgentResultRequest(
                jobId,
                "SUCCESS",
                List.of("hook_gap_observed", "structure_rhythm_draft"),
                null
        );

        // when: 模拟 agent-service 回调 Java 内部接口
        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/agent-results", jobId)
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(callback)))
                .andExpect(status().isOk());

        // then: HandleAgentResultCase 应将任务置为 COMPLETED
        AnalysisJob completedJob = analysisJobRepository.findById(jobId).orElseThrow();
        assertThat(completedJob.getStatus()).isEqualTo(JobStatusEnum.COMPLETED);
        assertThat(completedJob.getCurrentStage()).isEqualTo("COMPLETED");
        assertThat(completedJob.getProgress()).isEqualTo(100);
        // 骨架：可断言 draft 快照已持久化到 skillVersionSnapshotJson
        // assertThat(completedJob.getSkillVersionSnapshotJson()).contains("hook_gap_observed");
    }

    // -------------------------------------------------------------------------
    // 场景 ③：模拟 agent FAILED 回调 → 任务 FAILED + errorMessage 落库
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("③ agent 回调 FAILED 时，任务应置为 FAILED 并持久化错误信息")
    void shouldFailJobWhenAgentCallbackFailed() throws Exception {
        String jobId = seedRunningJob().getId();
        String errorMessage = "LLM quota exceeded";

        InternalAgentResultRequest callback = new InternalAgentResultRequest(
                jobId,
                "FAILED",
                List.of(),
                errorMessage
        );

        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/agent-results", jobId)
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(callback)))
                .andExpect(status().isOk());

        AnalysisJob failedJob = analysisJobRepository.findById(jobId).orElseThrow();
        assertThat(failedJob.getStatus()).isEqualTo(JobStatusEnum.FAILED);
        assertThat(failedJob.getCurrentStage()).isEqualTo("FAILED");
        assertThat(failedJob.getErrorMessage()).isEqualTo(errorMessage);
    }

    // -------------------------------------------------------------------------
    // 场景 ④：InternalApiAuthFilter —— 无 token 访问 /internal 返回 403
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("④ 未携带 X-Internal-Api-Key 访问 /internal 接口应返回 403")
    void shouldRejectInternalApiWithoutToken() throws Exception {
        String jobId = seedRunningJob().getId();

        InternalAgentResultRequest callback = new InternalAgentResultRequest(
                jobId,
                "SUCCESS",
                List.of("ignored"),
                null
        );

        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/agent-results", jobId)
                        // 故意不设置 X-Internal-Api-Key
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(callback)))
                .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("⑤ worker 应抢占 WAITING_AGENT 任务并 dispatch")
    void workerShouldDispatchWaitingJob() throws Exception {
        String jobId = seedWaitingAgentJob().getId();
        agentServiceMock.enqueue(new MockResponse().setResponseCode(202).setBody("{\"accepted\":true}"));

        boolean dispatched = dispatchAgentCase.dispatchOne(jobId);

        AnalysisJob job = analysisJobRepository.findById(jobId).orElseThrow();
        assertThat(dispatched).isTrue();
        assertThat(job.getStatus()).isEqualTo(JobStatusEnum.AGENT_RUNNING);
        assertThat(job.getCurrentAgentRunId()).isNotBlank();
        assertThat(job.getAgentTimeoutAt()).isAfter(LocalDateTime.now());
        awaitAgentHttpSubmit();
    }

    @Test
    @DisplayName("⑥ dispatch 失败后进入 RETRYING")
    void dispatchFailureShouldRetry() {
        String jobId = seedWaitingAgentJob().getId();
        agentServiceMock.enqueue(new MockResponse().setResponseCode(500).setBody("boom"));

        boolean dispatched = dispatchAgentCase.dispatchOne(jobId);

        AnalysisJob job = analysisJobRepository.findById(jobId).orElseThrow();
        assertThat(dispatched).isFalse();
        assertThat(job.getStatus()).isEqualTo(JobStatusEnum.RETRYING);
        assertThat(job.getRetryCount()).isEqualTo(1);
        assertThat(job.getNextRetryAt()).isNotNull();
    }

    @Test
    @DisplayName("⑦ 达到最大重试后 dispatch 失败应 FAILED")
    void dispatchFailureShouldFailAfterMaxRetry() {
        AnalysisJob seeded = seedWaitingAgentJob();
        seeded.setRetryCount(3);
        seeded.setMaxRetryCount(3);
        analysisJobRepository.save(seeded);
        agentServiceMock.enqueue(new MockResponse().setResponseCode(500).setBody("boom"));

        dispatchAgentCase.dispatchOne(seeded.getId());

        AnalysisJob job = analysisJobRepository.findById(seeded.getId()).orElseThrow();
        assertThat(job.getStatus()).isEqualTo(JobStatusEnum.FAILED);
    }

    @Test
    @DisplayName("⑧ timeout job 应进入 RETRYING")
    void timeoutJobShouldBeRecoveredToRetrying() {
        String jobId = seedAgentRunningJob("run-timeout", LocalDateTime.now().minusSeconds(1)).getId();

        boolean recovered = recoverTimedOutJobCase.recoverOne(jobId);

        AnalysisJob job = analysisJobRepository.findById(jobId).orElseThrow();
        assertThat(recovered).isTrue();
        assertThat(job.getStatus()).isEqualTo(JobStatusEnum.RETRYING);
        assertThat(job.getRetryCount()).isEqualTo(1);
    }

    @Test
    @DisplayName("⑨ 重复 callback 不应重复改变已完成任务")
    void duplicateCallbackShouldBeIdempotent() throws Exception {
        AnalysisJob running = seedAgentRunningJob("run-idem", LocalDateTime.now().plusMinutes(5));
        InternalAgentResultRequest callback = new InternalAgentResultRequest(
                running.getId(),
                "SUCCESS",
                "run-idem",
                1,
                List.of("first-result"),
                null
        );

        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/agent-results", running.getId())
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(callback)))
                .andExpect(status().isOk());
        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/agent-results", running.getId())
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(callback)))
                .andExpect(status().isOk());

        AnalysisJob completed = analysisJobRepository.findById(running.getId()).orElseThrow();
        assertThat(completed.getStatus()).isEqualTo(JobStatusEnum.COMPLETED);
        assertThat(completed.getLastResultVersion()).isEqualTo(1);
    }

    @Test
    @DisplayName("⑩ stale agentRunId callback 应被拒绝")
    void staleAgentRunCallbackShouldBeRejected() throws Exception {
        AnalysisJob running = seedAgentRunningJob("run-new", LocalDateTime.now().plusMinutes(5));
        InternalAgentResultRequest callback = new InternalAgentResultRequest(
                running.getId(),
                "SUCCESS",
                "run-old",
                1,
                List.of("late-result"),
                null
        );

        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/agent-results", running.getId())
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(callback)))
                .andExpect(status().isBadRequest());

        AnalysisJob job = analysisJobRepository.findById(running.getId()).orElseThrow();
        assertThat(job.getStatus()).isEqualTo(JobStatusEnum.AGENT_RUNNING);
    }

    @Test
    @DisplayName("⑪ 可按 jobId/agentRunId 查询轻量 Agent Trace")
    void shouldQueryAgentTraceByJobAndRun() throws Exception {
        AnalysisJob running = seedAgentRunningJob("run-trace", LocalDateTime.now().plusMinutes(5));
        InternalAgentResultRequest callback = new InternalAgentResultRequest(
                running.getId(),
                "SUCCESS",
                "run-trace",
                1,
                List.of("agent_run_status:COMPLETED"),
                List.of(Map.of(
                        "runId", "run-trace",
                        "stepType", "HOOK_ANALYSIS",
                        "skillCode", "hook_analysis",
                        "toolName", "retrieve_knowledge",
                        "evidenceRefs", List.of("FRAME:target-1", "KNOWLEDGE:hook-pattern-opening-pain-v1"),
                        "latencyMs", 12,
                        "status", "SUCCESS",
                        "shortSummary", "Hook analysis completed"
                )),
                null
        );

        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/agent-results", running.getId())
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(callback)))
                .andExpect(status().isOk());

        mockMvc.perform(get("/internal/v1/analysis/jobs/{jobId}/agent-runs/{agentRunId}/trace", running.getId(), "run-trace")
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.jobId").value(running.getId()))
                .andExpect(jsonPath("$.data.agentRunId").value("run-trace"))
                .andExpect(jsonPath("$.data.steps[0].stepType").value("HOOK_ANALYSIS"))
                .andExpect(jsonPath("$.data.steps[0].skillCode").value("hook_analysis"))
                .andExpect(jsonPath("$.data.steps[0].shortSummary").value("Hook analysis completed"));
    }

    @Test
    @DisplayName("⑫ 批量保存结论：同一个 idempotencyKey 重复提交不会重复写入 Finding")
    void diagnosisResultBatchSaveShouldBeIdempotent() throws Exception {
        AnalysisJob running = seedAgentRunningJob("run-batch", LocalDateTime.now().plusMinutes(5));
        String body = objectMapper.writeValueAsString(diagnosisResultBody(running.getId(), "run-batch:v1"));

        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/diagnosis-results", running.getId())
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.duplicate").value(false))
                .andExpect(jsonPath("$.data.findingIds.length()").value(2));

        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/diagnosis-results", running.getId())
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.duplicate").value(true))
                .andExpect(jsonPath("$.data.findingIds.length()").value(2));

        List<Finding> findings = findingRepository.findByJobId(running.getId());
        assertThat(findings).hasSize(2);
        assertThat(findings).extracting(Finding::getStatus).containsExactlyInAnyOrder("agent", "agent_abstain");
        assertThat(findings)
                .filteredOn(finding -> "agent".equals(finding.getStatus()))
                .extracting(Finding::getPriority)
                .containsExactly(PriorityEnum.P2);
    }

    @Test
    @DisplayName("⑬ 合成结论可以通过公开接口查询")
    void synthesisShouldBeQueryable() throws Exception {
        AnalysisJob running = seedAgentRunningJob("run-synthesis", LocalDateTime.now().plusMinutes(5));

        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/diagnosis-results", running.getId())
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(diagnosisResultBody(running.getId(), "run-synthesis:v1"))))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/v1/analysis/jobs/{jobId}/synthesis", running.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.summary").value("最优先改进开场钩子"))
                .andExpect(jsonPath("$.data.priorities[0].skillKey").value("hook_analysis"));
    }

    @Test
    @DisplayName("⑭ 批量接口路径与 body 中的 jobId 不一致时拒绝")
    void diagnosisResultWithMismatchedJobIdShouldBeRejected() throws Exception {
        AnalysisJob running = seedAgentRunningJob("run-mismatch", LocalDateTime.now().plusMinutes(5));

        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/diagnosis-results", running.getId())
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(diagnosisResultBody("other-job", "run-mismatch:v1"))))
                .andExpect(status().isBadRequest());
    }

    // -------------------------------------------------------------------------
    // 可靠性修复的回归用例（⑮~⑲）
    // -------------------------------------------------------------------------

    @Test
    @DisplayName("⑮ 派发请求带 X-Trace-Id = agentRunId，派发结束后 MDC 已清理")
    void dispatchShouldPropagateAgentRunIdAsTraceId() throws Exception {
        String jobId = seedWaitingAgentJob().getId();
        agentServiceMock.enqueue(new MockResponse().setResponseCode(202).setBody("{\"accepted\":true}"));

        assertThat(dispatchAgentCase.dispatchOne(jobId)).isTrue();

        RecordedRequest submitted = agentServiceMock.takeRequest(2, TimeUnit.SECONDS);
        AnalysisJob job = analysisJobRepository.findById(jobId).orElseThrow();
        assertThat(submitted).isNotNull();
        assertThat(submitted.getHeader("X-Trace-Id")).isEqualTo(job.getCurrentAgentRunId());
        assertThat(MDC.get("traceId")).isNull();
        assertThat(MDC.get("jobId")).isNull();
    }

    @Test
    @DisplayName("⑯ 回调沿用请求头里的 traceId；不安全的 traceId 被替换")
    void callbackShouldReuseTraceIdHeader() throws Exception {
        AnalysisJob running = seedAgentRunningJob("run-traced", LocalDateTime.now().plusMinutes(5));
        InternalAgentResultRequest callback = new InternalAgentResultRequest(
                running.getId(), "SUCCESS", "run-traced", 1, List.of("ok"), null);

        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/agent-results", running.getId())
                        .header(INTERNAL_API_KEY_HEADER, INTERNAL_API_KEY)
                        .header("X-Trace-Id", "run-traced")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(callback)))
                .andExpect(status().isOk())
                .andExpect(header().string("X-Trace-Id", "run-traced"))
                .andExpect(jsonPath("$.traceId").value("run-traced"));

        // 带换行的值可能伪造日志行：不采用，新生成一个
        mockMvc.perform(post("/internal/v1/analysis/jobs/{jobId}/agent-results", running.getId())
                        .header("X-Trace-Id", "x\nINFO forged log line")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(callback)))
                .andExpect(status().isForbidden())
                .andExpect(header().string("X-Trace-Id", matchesPattern("[0-9a-f]{32}")));
    }

    @Test
    @DisplayName("⑰ HTTP 失败但回调已先到并完成任务：不能再把任务改成 RETRYING")
    void dispatchFailureAfterFastCallbackShouldKeepCompletedJob() throws Exception {
        AnalysisJob seeded = seedWaitingAgentJob();
        agentServiceMock.setDispatcher(new Dispatcher() {
            @Override
            public MockResponse dispatch(RecordedRequest request) {
                // agent-service 已收到任务并很快回调成功，但给 Java 的 HTTP 响应失败了（读超时 / 网关 502）
                AnalysisJob job = analysisJobRepository.findById(seeded.getId()).orElseThrow();
                job.startResultProcessing();
                job.complete(job.getCurrentAgentRunId(), 1);
                analysisJobRepository.save(job);
                return new MockResponse().setResponseCode(502);
            }
        });
        try {
            assertThat(dispatchAgentCase.dispatchOne(seeded.getId())).isFalse();
        } finally {
            agentServiceMock.setDispatcher(new QueueDispatcher());
        }

        AnalysisJob job = analysisJobRepository.findById(seeded.getId()).orElseThrow();
        assertThat(job.getStatus()).isEqualTo(JobStatusEnum.COMPLETED);
        assertThat(job.getRetryCount()).isZero();
    }

    @Test
    @DisplayName("⑱ 任务已被别的 worker 抢走：跳过，不发请求、不改它")
    void dispatchShouldSkipJobClaimedByAnotherWorker() {
        AnalysisJob running = seedAgentRunningJob("run-other-worker", LocalDateTime.now().plusMinutes(5));
        int requestsBefore = agentServiceMock.getRequestCount();

        assertThat(dispatchAgentCase.dispatchOne(running.getId())).isFalse();

        AnalysisJob job = analysisJobRepository.findById(running.getId()).orElseThrow();
        assertThat(job.getStatus()).isEqualTo(JobStatusEnum.AGENT_RUNNING);
        assertThat(job.getCurrentAgentRunId()).isEqualTo("run-other-worker");
        assertThat(job.getRetryCount()).isZero();
        assertThat(agentServiceMock.getRequestCount()).isEqualTo(requestsBefore);
    }

    @Test
    @DisplayName("⑲ 超时扫描到之后回调先完成了任务：回收时跳过，不抛异常")
    void timeoutRecoveryShouldSkipJobCompletedMeanwhile() {
        AnalysisJob job = seedAgentRunningJob("run-late-done", LocalDateTime.now().minusSeconds(1));
        job.startResultProcessing();
        job.complete("run-late-done", 1);
        analysisJobRepository.save(job);

        assertThat(recoverTimedOutJobCase.recoverOne(job.getId())).isFalse();

        AnalysisJob reloaded = analysisJobRepository.findById(job.getId()).orElseThrow();
        assertThat(reloaded.getStatus()).isEqualTo(JobStatusEnum.COMPLETED);
        assertThat(reloaded.getRetryCount()).isZero();
    }

    private Map<String, Object> diagnosisResultBody(String jobId, String idempotencyKey) {
        Map<String, Object> hook = Map.of(
                "jobId", jobId,
                "skillKey", "hook_analysis",
                "dimension", "HOOK",
                "outcome", "FINDING",
                "observation", "开场 3 秒没有收益承诺",
                "suggestedAction", "第 1 秒直接给出结果画面",
                "evidenceRefs", List.of("00:00:00-00:00:03", "OCR:target-1"),
                "confidence", 0.88,
                // agent 按合成排序给的优先级；旧规则下 0.88 会被判成 P0
                "priority", "P2"
        );
        Map<String, Object> value = Map.of(
                "jobId", jobId,
                "skillKey", "value_delivery_analysis",
                "dimension", "VALUE_DELIVERY",
                "outcome", "ABSTAIN",
                "observation", "缺少可判断收益的文字证据",
                "suggestedAction", "补充证据后再诊断",
                "confidence", 0.0
        );
        return Map.of(
                "jobId", jobId,
                "agentRunId", idempotencyKey.split(":")[0],
                "resultVersion", 1,
                "idempotencyKey", idempotencyKey,
                "findings", List.of(hook, value),
                "synthesis", Map.of(
                        "summary", "最优先改进开场钩子",
                        "priorities", List.of(Map.of("rank", 1, "skillKey", "hook_analysis"))
                )
        );
    }

    // -------------------------------------------------------------------------
    // 测试数据构造（直接写仓储，绕过完整上传/建任务流程，聚焦 Agent 链路）
    // -------------------------------------------------------------------------

    private AnalysisJob seedPendingJob() {
        return analysisJobRepository.save(buildJob(JobStatusEnum.PENDING, "PENDING", 0));
    }

    private AnalysisJob seedRunningJob() {
        AnalysisJob job = buildJob(JobStatusEnum.RUNNING, "RUNNING", 10);
        job.setStartedAt(LocalDateTime.now());
        return analysisJobRepository.save(job);
    }

    private AnalysisJob seedWaitingAgentJob() {
        AnalysisJob job = buildJob(JobStatusEnum.WAITING_AGENT, "WAITING_AGENT", 40);
        job.setNextRetryAt(LocalDateTime.now().minusSeconds(1));
        job.setMaxRetryCount(3);
        return analysisJobRepository.save(job);
    }

    private AnalysisJob seedAgentRunningJob(String agentRunId, LocalDateTime timeoutAt) {
        AnalysisJob job = buildJob(JobStatusEnum.AGENT_RUNNING, "AGENT_RUNNING", 60);
        job.setCurrentAgentRunId(agentRunId);
        job.setAgentStartedAt(LocalDateTime.now().minusMinutes(1));
        job.setAgentTimeoutAt(timeoutAt);
        job.setMaxRetryCount(3);
        return analysisJobRepository.save(job);
    }

    private AnalysisJob buildJob(JobStatusEnum status, String stage, int progress) {
        AnalysisJob job = new AnalysisJob();
        String id = UUID.randomUUID().toString();
        job.setId(id);
        job.setJobKey("integration-test-" + id);
        job.setTargetVideoId("video-target-1");
        job.setReferenceVideoIds(List.of("video-ref-1"));
        job.setStatus(status);
        job.setProgress(progress);
        job.setCurrentStage(stage);
        job.setInputSnapshotJson("{\"targetVideoId\":\"video-target-1\"}");
        job.setCreatedAt(LocalDateTime.now());
        job.setUpdatedAt(LocalDateTime.now());
        return job;
    }

    /**
     * 等待 AgentServiceHttpClient 虚拟线程完成 HTTP 提交。
     * 骨架实现：生产测试建议替换为 Awaitility.await() 轮询 MockWebServer.getRequestCount()。
     */
    private void awaitAgentHttpSubmit() throws InterruptedException {
        Thread.sleep(500);
    }
}
