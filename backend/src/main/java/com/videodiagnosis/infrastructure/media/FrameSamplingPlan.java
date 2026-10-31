package com.videodiagnosis.infrastructure.media;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * 关键帧采样计划（纯函数，便于单测）。
 *
 * <ul>
 *   <li>hook：开场 [0, hookDenseSeconds) 每 hookStep 秒一帧，服务开场钩子分析；</li>
 *   <li>interval：之后每 step 秒一帧，覆盖整个分析窗口；</li>
 *   <li>scene：镜头切换点，和已有采样点距离 &gt;= mergeSeconds 才补帧，服务结构节奏分析；</li>
 *   <li>end：窗口末尾一帧，服务价值传递 / 结尾 CTA 分析。</li>
 * </ul>
 * 超过 maxFrames 时保留全部 hook 与 end，其余按时间均匀抽稀。
 */
public final class FrameSamplingPlan {

    public static final String HOOK = "hook";
    public static final String INTERVAL = "interval";
    public static final String SCENE = "scene";
    public static final String END = "end";

    private FrameSamplingPlan() {
    }

    public record Sample(double seconds, String reason) {
    }

    public static List<Sample> plan(double windowSeconds,
                                    double hookDenseSeconds,
                                    double hookStep,
                                    double step,
                                    List<Double> sceneChanges,
                                    double mergeSeconds,
                                    int maxFrames) {
        List<Sample> samples = new ArrayList<>();
        if (windowSeconds <= 0) {
            samples.add(new Sample(0, HOOK));
            return samples;
        }
        double safeHookStep = hookStep > 0 ? hookStep : 1.0;
        double safeStep = step > 0 ? step : 3.0;
        double hookEnd = Math.min(Math.max(0, hookDenseSeconds), windowSeconds);

        for (double t = 0; t < hookEnd - 1e-6; t += safeHookStep) {
            samples.add(new Sample(round(t), HOOK));
        }
        if (samples.isEmpty()) {
            samples.add(new Sample(0, HOOK));
        }
        for (double t = hookEnd; t < windowSeconds - 1e-6; t += safeStep) {
            addIfFar(samples, new Sample(round(t), INTERVAL), 0.25);
        }
        if (sceneChanges != null) {
            for (Double change : sceneChanges) {
                // 切换点后 0.3 秒取帧，保证拍到的是新镜头而不是转场中间帧
                double at = change == null ? -1 : Math.min(change + 0.3, windowSeconds - 0.1);
                if (change != null && change > 0 && at < windowSeconds) {
                    addIfFar(samples, new Sample(round(at), SCENE), mergeSeconds);
                }
            }
        }
        double end = Math.max(0, windowSeconds - 0.5);
        addIfFar(samples, new Sample(round(end), END), Math.min(mergeSeconds, 0.5));

        samples.sort(Comparator.comparingDouble(Sample::seconds));
        return limit(samples, maxFrames);
    }

    private static void addIfFar(List<Sample> samples, Sample candidate, double minDistance) {
        for (Sample existing : samples) {
            if (Math.abs(existing.seconds() - candidate.seconds()) < minDistance) {
                return;
            }
        }
        samples.add(candidate);
    }

    private static List<Sample> limit(List<Sample> samples, int maxFrames) {
        if (maxFrames <= 0 || samples.size() <= maxFrames) {
            return samples;
        }
        List<Sample> keep = new ArrayList<>();
        List<Sample> rest = new ArrayList<>();
        for (Sample sample : samples) {
            if (HOOK.equals(sample.reason()) || END.equals(sample.reason())) {
                keep.add(sample);
            } else {
                rest.add(sample);
            }
        }
        int budget = Math.max(0, maxFrames - keep.size());
        if (budget > 0 && !rest.isEmpty()) {
            double stride = (double) rest.size() / budget;
            for (int i = 0; i < budget; i++) {
                keep.add(rest.get(Math.min(rest.size() - 1, (int) Math.floor(i * stride))));
            }
        }
        keep.sort(Comparator.comparingDouble(Sample::seconds));
        return keep.size() > maxFrames ? new ArrayList<>(keep.subList(0, maxFrames)) : keep;
    }

    private static double round(double seconds) {
        return Math.round(seconds * 10.0) / 10.0;
    }
}
