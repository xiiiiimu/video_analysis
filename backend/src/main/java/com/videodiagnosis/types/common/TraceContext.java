package com.videodiagnosis.types.common;

import org.slf4j.MDC;

import java.util.UUID;
import java.util.regex.Pattern;

/**
 * 链路追踪上下文（基于 SLF4J MDC）。
 *
 * <p>约定：
 * <ul>
 *   <li>HTTP 请求：{@code X-Trace-Id} 请求头有合法值就沿用，否则新生成；响应头和 {@link Result#traceId()} 返回同一个值。</li>
 *   <li>Agent 派发：一次派发就是一条链路，traceId 直接用 agentRunId。Java 派发请求、agent-service 的日志、
 *       agent-service 回调 Java 的请求都带这个值，所以按 agentRunId 能把两个服务的日志串起来。</li>
 * </ul>
 * 日志格式里通过 {@code %X{traceId}} / {@code %X{jobId}} 输出（见 application.yml 的 logging.pattern.level）。
 */
public final class TraceContext {

    public static final String HEADER = "X-Trace-Id";
    public static final String TRACE_ID = "traceId";
    public static final String JOB_ID = "jobId";

    /** 外部传入的值只接受这些字符：防止通过请求头往日志里注入换行、伪造日志行。 */
    private static final Pattern SAFE_VALUE = Pattern.compile("[A-Za-z0-9_.:-]{1,64}");

    private TraceContext() {
    }

    public static String newTraceId() {
        return UUID.randomUUID().toString().replace("-", "");
    }

    /** 合法则原样返回，否则返回 null（由调用方决定是否新生成）。 */
    public static String sanitize(String candidate) {
        return candidate != null && SAFE_VALUE.matcher(candidate).matches() ? candidate : null;
    }

    /** 当前线程的 traceId；不在任何链路里时返回 null。 */
    public static String currentTraceId() {
        return MDC.get(TRACE_ID);
    }

    /** 当前 traceId，没有就新生成一个（不写入 MDC）。 */
    public static String currentOrNew() {
        String current = currentTraceId();
        return current == null || current.isBlank() ? newTraceId() : current;
    }

    /**
     * 打开一个作用域：写入 traceId / jobId，close 时恢复成进入前的值。
     * 定时任务一次扫描处理多个任务时，每个任务各自一个作用域，互不串值；线程池线程复用也不会残留。
     */
    public static Scope open(String traceId, String jobId) {
        return new Scope(traceId, jobId);
    }

    public static final class Scope implements AutoCloseable {

        private final String previousTraceId;
        private final String previousJobId;

        private Scope(String traceId, String jobId) {
            this.previousTraceId = MDC.get(TRACE_ID);
            this.previousJobId = MDC.get(JOB_ID);
            put(TRACE_ID, traceId);
            put(JOB_ID, jobId);
        }

        @Override
        public void close() {
            put(TRACE_ID, previousTraceId);
            put(JOB_ID, previousJobId);
        }

        private static void put(String key, String value) {
            if (value == null || value.isBlank()) {
                MDC.remove(key);
            } else {
                MDC.put(key, value);
            }
        }
    }
}
