package com.videodiagnosis.infrastructure.redis;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * 回调去重标记：只有数据库事务提交后才算"处理过"；本机兜底有过期时间和条数上限。
 * 不连 Redis（redisTemplate 为 null 时走本机兜底，逻辑与 Redis 分支一致）。
 */
class RedisIdempotencyRepositoryTest {

    private final RedisIdempotencyRepository repository =
            new RedisIdempotencyRepository(null, 100, Clock.systemUTC());

    @AfterEach
    void clearSynchronization() {
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.clearSynchronization();
        }
    }

    @Test
    void markIsDeferredUntilCommit() {
        TransactionSynchronizationManager.initSynchronization();

        repository.markProcessedAfterCommit("run-1", 1);
        assertThat(repository.alreadyProcessed("run-1", 1)).isFalse();

        TransactionSynchronizationManager.getSynchronizations().forEach(TransactionSynchronization::afterCommit);
        assertThat(repository.alreadyProcessed("run-1", 1)).isTrue();
    }

    @Test
    void rollbackLeavesCallbackRetryable() {
        TransactionSynchronizationManager.initSynchronization();

        repository.markProcessedAfterCommit("run-2", 1);
        // 事务回滚：afterCommit 不会被调用
        TransactionSynchronizationManager.getSynchronizations()
                .forEach(sync -> sync.afterCompletion(TransactionSynchronization.STATUS_ROLLED_BACK));

        assertThat(repository.alreadyProcessed("run-2", 1)).isFalse();
    }

    @Test
    void marksImmediatelyWithoutTransaction() {
        repository.markProcessedAfterCommit("run-3", 1);
        assertThat(repository.alreadyProcessed("run-3", 1)).isTrue();
        assertThat(repository.alreadyProcessed("run-3", 2)).isFalse();
    }

    @Test
    void localFallbackIsBounded() {
        RedisIdempotencyRepository small = new RedisIdempotencyRepository(null, 10, Clock.systemUTC());
        for (int i = 0; i < 1_000; i++) {
            small.markProcessed("run-" + i, 1);
        }
        assertThat(small.localFallbackSize()).isLessThanOrEqualTo(10);
        assertThat(small.alreadyProcessed("run-999", 1)).isTrue();
    }

    @Test
    void localFallbackEntriesExpire() {
        MutableClock clock = new MutableClock(Instant.parse("2026-10-30T00:00:00Z"));
        RedisIdempotencyRepository expiring = new RedisIdempotencyRepository(null, 100, clock);
        expiring.markProcessed("run-old", 1);
        assertThat(expiring.alreadyProcessed("run-old", 1)).isTrue();

        clock.advance(RedisIdempotencyRepository.TTL.plus(Duration.ofSeconds(1)));
        assertThat(expiring.alreadyProcessed("run-old", 1)).isFalse();
        assertThat(expiring.localFallbackSize()).isZero();
    }

    private static final class MutableClock extends Clock {
        private Instant now;

        private MutableClock(Instant now) {
            this.now = now;
        }

        void advance(Duration duration) {
            now = now.plus(duration);
        }

        @Override
        public ZoneOffset getZone() {
            return ZoneOffset.UTC;
        }

        @Override
        public Clock withZone(java.time.ZoneId zone) {
            return this;
        }

        @Override
        public Instant instant() {
            return now;
        }
    }
}
