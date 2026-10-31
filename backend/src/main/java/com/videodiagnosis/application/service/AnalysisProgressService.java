package com.videodiagnosis.application.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.application.view.AnalysisProgressSnapshot;
import com.videodiagnosis.domain.entity.AnalysisJob;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Optional;

@Service
public class AnalysisProgressService {

    private static final Logger log = LoggerFactory.getLogger(AnalysisProgressService.class);
    private static final String KEY_PREFIX = "analysis:job:";
    private static final String KEY_SUFFIX = ":progress";

    private final ObjectMapper objectMapper;
    private final StringRedisTemplate redisTemplate;

    public AnalysisProgressService(ObjectMapper objectMapper,
                                   ObjectProvider<StringRedisTemplate> redisTemplateProvider) {
        this.objectMapper = objectMapper;
        this.redisTemplate = redisTemplateProvider.getIfAvailable();
    }

    public void updateProgress(String jobId, String stage, int percent, String status) {
        updateProgress(jobId, stage, percent, status, null, null);
    }

    public void updateProgress(String jobId,
                               String stage,
                               int percent,
                               String status,
                               String agentRunId,
                               String shortSummary) {
        if (redisTemplate == null) {
            return;
        }
        AnalysisProgressSnapshot snapshot = new AnalysisProgressSnapshot(
                jobId,
                status,
                percent,
                stage,
                LocalDateTime.now(),
                agentRunId,
                shortSummary
        );
        try {
            Duration ttl = "COMPLETED".equals(status) || "FAILED".equals(status)
                    ? Duration.ofMinutes(30)
                    : Duration.ofMinutes(10);
            redisTemplate.opsForValue().set(key(jobId), objectMapper.writeValueAsString(snapshot), ttl);
        } catch (Exception ex) {
            log.warn("redis progress update failed jobId={}", jobId, ex);
        }
    }

    public Optional<AnalysisProgressSnapshot> getProgress(String jobId) {
        if (redisTemplate == null) {
            return Optional.empty();
        }
        try {
            String json = redisTemplate.opsForValue().get(key(jobId));
            if (json == null || json.isBlank()) {
                log.debug("redis progress miss jobId={}", jobId);
                return Optional.empty();
            }
            log.debug("redis progress hit jobId={}", jobId);
            return Optional.of(objectMapper.readValue(json, AnalysisProgressSnapshot.class));
        } catch (JsonProcessingException ex) {
            log.warn("redis progress parse failed jobId={}", jobId, ex);
            return Optional.empty();
        } catch (Exception ex) {
            log.warn("redis progress read failed jobId={}", jobId, ex);
            return Optional.empty();
        }
    }

    public void invalidate(String jobId) {
        if (redisTemplate == null) {
            return;
        }
        try {
            redisTemplate.delete(key(jobId));
        } catch (Exception ex) {
            log.warn("redis progress invalidate failed jobId={}", jobId, ex);
        }
    }

    public AnalysisProgressSnapshot fromJob(AnalysisJob job) {
        return new AnalysisProgressSnapshot(
                job.getId(),
                String.valueOf(job.getStatus()),
                job.getProgress(),
                job.getCurrentStage(),
                job.getUpdatedAt()
        );
    }

    private String key(String jobId) {
        return KEY_PREFIX + jobId + KEY_SUFFIX;
    }
}
