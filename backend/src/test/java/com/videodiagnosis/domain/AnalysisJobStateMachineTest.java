package com.videodiagnosis.domain;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.exception.InvalidJobStateTransitionException;
import com.videodiagnosis.types.enums.JobStatusEnum;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class AnalysisJobStateMachineTest {

    @Test
    void shouldTransitThroughAgentLifecycle() {
        AnalysisJob job = new AnalysisJob();
        job.setId("job-1");
        job.setStatus(JobStatusEnum.CREATED);

        job.waitForAgent(LocalDateTime.now());
        job.markAgentRunning("run-1", LocalDateTime.now().plusMinutes(10));
        job.startResultProcessing();
        job.complete("run-1", 1);

        assertThat(job.getStatus()).isEqualTo(JobStatusEnum.COMPLETED);
        assertThat(job.getProgress()).isEqualTo(100);
        assertThat(job.getLastProcessedAgentRunId()).isEqualTo("run-1");
        assertThat(job.getLastResultVersion()).isEqualTo(1);
    }

    @Test
    void shouldRejectIllegalTransitionAfterCompleted() {
        AnalysisJob job = new AnalysisJob();
        job.setId("job-2");
        job.setStatus(JobStatusEnum.COMPLETED);

        assertThatThrownBy(() -> job.markAgentRunning("run-2", LocalDateTime.now().plusMinutes(10)))
                .isInstanceOf(InvalidJobStateTransitionException.class);
    }

    @Test
    void completedJobShouldNotBeFailedAgain() {
        AnalysisJob job = new AnalysisJob();
        job.setId("job-3");
        job.setStatus(JobStatusEnum.COMPLETED);

        assertThatThrownBy(() -> job.markFailed("ERR", "late failure"))
                .isInstanceOf(InvalidJobStateTransitionException.class);
    }
}
