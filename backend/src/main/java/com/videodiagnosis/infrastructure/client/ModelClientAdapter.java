package com.videodiagnosis.infrastructure.client;

import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.types.enums.AnalysisDimensionEnum;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * @deprecated LLM 调用已迁移至 Python agent-service。
 * 当前类仅保留占位实现，供过渡期 RevisionPlanWorkflow / BuildResultCase 使用。
 * 后续应改为通过 HTTP 调用 agent-service，或删除 summarize/infer 入口。
 */
@Deprecated
@Component
public class ModelClientAdapter {

    public String inferObservation(AnalysisDimensionEnum dimension, VideoFeature target, List<VideoFeature> references) {
        int targetLength = target == null || target.getTranscriptText() == null ? 0 : target.getTranscriptText().length();
        int referenceCount = references == null ? 0 : references.size();
        return "Model summary for " + dimension + " with target text length " + targetLength + " and " + referenceCount + " reference videos.";
    }

    public String summarizeFindings(List<Finding> findings) {
        if (findings == null || findings.isEmpty()) {
            return "No core issue was found.";
        }
        return findings.stream()
                .map(finding -> finding.getDimension() + ":" + finding.getSuggestedAction())
                .limit(3)
                .reduce((left, right) -> left + " | " + right)
                .orElse("No core issue was found.");
    }
}
