package com.videodiagnosis.interfaces.observability;

import com.videodiagnosis.types.common.TraceContext;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 每个 HTTP 请求进入时绑定 traceId（和路径里的 jobId）到 MDC，请求结束清理。
 *
 * <p>排在最前面（早于内部接口鉴权），这样鉴权失败的日志也带 traceId。
 * agent-service 回调时请求头带 {@code X-Trace-Id = agentRunId}，所以回调处理日志和派发日志是同一个 traceId。
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TraceIdFilter extends OncePerRequestFilter {

    private static final Pattern JOB_PATH = Pattern.compile("/jobs/([A-Za-z0-9-]{1,64})(?:/|$)");

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String traceId = TraceContext.sanitize(request.getHeader(TraceContext.HEADER));
        if (traceId == null) {
            traceId = TraceContext.newTraceId();
        }
        response.setHeader(TraceContext.HEADER, traceId);
        try (TraceContext.Scope ignored = TraceContext.open(traceId, jobIdFromPath(request.getRequestURI()))) {
            filterChain.doFilter(request, response);
        }
    }

    static String jobIdFromPath(String uri) {
        if (uri == null) {
            return null;
        }
        Matcher matcher = JOB_PATH.matcher(uri);
        return matcher.find() ? matcher.group(1) : null;
    }
}
