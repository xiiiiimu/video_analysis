package com.videodiagnosis.types.common;

public record Result<T>(boolean success, T data, String error, String traceId) {

    public static <T> Result<T> ok(T data) {
        return new Result<>(true, data, null, newTraceId());
    }

    public static <T> Result<T> fail(ErrorCode errorCode) {
        return new Result<>(false, null, errorCode.getMessage(), newTraceId());
    }

    public static <T> Result<T> fail(String message) {
        return new Result<>(false, null, message, newTraceId());
    }

    /**
     * 原来每次随机生成，除了异常处理器打的那一行，和这次请求的其它日志都对不上；
     * 现在取当前请求 MDC 里的 traceId，响应里的 traceId 能搜到这次请求的全部日志
     *（agent 回调请求的 traceId 就是 agentRunId，还能接上 agent-service 那边的日志）。
     */
    private static String newTraceId() {
        return TraceContext.currentOrNew();
    }
}