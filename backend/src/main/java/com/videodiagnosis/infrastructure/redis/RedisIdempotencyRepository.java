package com.videodiagnosis.infrastructure.redis;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.Clock;
import java.time.Duration;
import java.util.Iterator;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 回调去重的快速路径。它只是缓存：真正的兜底是回调记录表 (agent_run_id, result_version) 唯一索引，
 * 所以这里宁可漏判（多查一次库），也不能误判（把没处理过的回调当成重复丢掉）。
 */
@Repository
public class RedisIdempotencyRepository {

    private static final Logger log = LoggerFactory.getLogger(RedisIdempotencyRepository.class);
    private static final String PREFIX = "agent:callback:idempotency:";
    static final Duration TTL = Duration.ofHours(6);
    static final int DEFAULT_MAX_LOCAL_ENTRIES = 10_000;

    private final StringRedisTemplate redisTemplate;
    /**
     * Redis 不可用时的本机兜底：key → 过期时刻（毫秒）。
     * 原来是一个永不清理的 Set，进程跑得越久越大；现在带过期时间并限制条数。
     */
    private final Map<String, Long> localFallback = new ConcurrentHashMap<>();
    private final int maxLocalEntries;
    private final Clock clock;

    @Autowired
    public RedisIdempotencyRepository(ObjectProvider<StringRedisTemplate> redisTemplateProvider) {
        this(redisTemplateProvider.getIfAvailable(), DEFAULT_MAX_LOCAL_ENTRIES, Clock.systemUTC());
    }

    RedisIdempotencyRepository(StringRedisTemplate redisTemplate, int maxLocalEntries, Clock clock) {
        this.redisTemplate = redisTemplate;
        this.maxLocalEntries = maxLocalEntries;
        this.clock = clock;
    }

    public boolean alreadyProcessed(String agentRunId, int resultVersion) {
        String key = key(agentRunId, resultVersion);
        if (redisTemplate == null) {
            return inLocalFallback(key);
        }
        try {
            return Boolean.TRUE.equals(redisTemplate.hasKey(key));
        } catch (Exception ex) {
            log.warn("redis idempotency read failed key={}", key, ex);
            return inLocalFallback(key);
        }
    }

    /**
     * 在当前事务提交之后再标记"已处理"；回滚则不标记。没有事务时立即标记。
     */
    public void markProcessedAfterCommit(String agentRunId, int resultVersion) {
        if (!TransactionSynchronizationManager.isSynchronizationActive()) {
            markProcessed(agentRunId, resultVersion);
            return;
        }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                markProcessed(agentRunId, resultVersion);
            }
        });
    }

    public void markProcessed(String agentRunId, int resultVersion) {
        String key = key(agentRunId, resultVersion);
        rememberLocally(key);
        if (redisTemplate == null) {
            return;
        }
        try {
            redisTemplate.opsForValue().set(key, "1", TTL);
        } catch (Exception ex) {
            log.warn("redis idempotency write failed key={}", key, ex);
        }
    }

    int localFallbackSize() {
        return localFallback.size();
    }

    private boolean inLocalFallback(String key) {
        Long expiresAt = localFallback.get(key);
        if (expiresAt == null) {
            return false;
        }
        if (expiresAt <= clock.millis()) {
            localFallback.remove(key, expiresAt);
            return false;
        }
        return true;
    }

    private void rememberLocally(String key) {
        long now = clock.millis();
        if (localFallback.size() >= maxLocalEntries) {
            localFallback.entrySet().removeIf(entry -> entry.getValue() <= now);
            // 还是满的就随便淘汰一些：这里只是缓存，漏判会落到数据库唯一索引上，不会重复处理
            Iterator<String> keys = localFallback.keySet().iterator();
            while (localFallback.size() >= maxLocalEntries && keys.hasNext()) {
                keys.next();
                keys.remove();
            }
        }
        localFallback.put(key, now + TTL.toMillis());
    }

    private String key(String agentRunId, int resultVersion) {
        return PREFIX + agentRunId + ":" + resultVersion;
    }
}
