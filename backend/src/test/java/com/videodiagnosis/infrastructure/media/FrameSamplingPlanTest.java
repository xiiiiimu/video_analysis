package com.videodiagnosis.infrastructure.media;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class FrameSamplingPlanTest {

    @Test
    void twoMinuteVideoIsCoveredWithDenseHookAndEndFrame() {
        List<FrameSamplingPlan.Sample> plan = FrameSamplingPlan.plan(120, 5, 1, 3, List.of(30.2), 1.0, 60);

        assertThat(plan).extracting(FrameSamplingPlan.Sample::seconds).startsWith(0.0, 1.0, 2.0, 3.0, 4.0);
        assertThat(plan.get(plan.size() - 1).reason()).isEqualTo(FrameSamplingPlan.END);
        assertThat(plan.get(plan.size() - 1).seconds()).isGreaterThan(100);
        assertThat(plan).anyMatch(sample -> FrameSamplingPlan.SCENE.equals(sample.reason()));
        assertThat(plan).isSortedAccordingTo((a, b) -> Double.compare(a.seconds(), b.seconds()));
    }

    @Test
    void frameCountIsCappedButHookAndEndAreKept() {
        List<Double> cuts = new ArrayList<>();
        for (int i = 1; i < 119; i++) {
            cuts.add(i + 0.5);
        }
        List<FrameSamplingPlan.Sample> plan = FrameSamplingPlan.plan(120, 5, 1, 3, cuts, 1.0, 60);

        assertThat(plan).hasSize(60);
        assertThat(plan).filteredOn(sample -> FrameSamplingPlan.HOOK.equals(sample.reason())).hasSize(5);
        assertThat(plan.get(plan.size() - 1).reason()).isEqualTo(FrameSamplingPlan.END);
    }

    @Test
    void timestampsBeyondOneMinuteAreFormattedCorrectly() {
        assertThat(FfmpegMediaAdapter.formatTimestamp(63.7)).isEqualTo("00:01:03");
        assertThat(FfmpegMediaAdapter.formatTimestamp(3725)).isEqualTo("01:02:05");
    }
}
