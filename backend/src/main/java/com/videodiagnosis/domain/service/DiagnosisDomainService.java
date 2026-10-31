package com.videodiagnosis.domain.service;

import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.valueobject.Evidence;
import com.videodiagnosis.domain.valueobject.Hypothesis;
import com.videodiagnosis.types.enums.AnalysisDimensionEnum;
import com.videodiagnosis.types.enums.PriorityEnum;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Service
public class DiagnosisDomainService {

    public List<Finding> diagnose(String jobId, VideoFeature targetFeature, List<VideoFeature> referenceFeatures) {
        List<Finding> findings = new ArrayList<>();
        String targetText = normalize(targetFeature == null ? null : targetFeature.getTextForDiagnosis());
        double referenceAverage = referenceFeatures == null || referenceFeatures.isEmpty()
                ? 1.0
                : referenceFeatures.stream()
                .map(VideoFeature::getTextForDiagnosis)
                .map(this::normalize)
                .mapToInt(String::length)
                .average()
                .orElse(1.0);

        if (targetText.isBlank() || targetText.length() > referenceAverage * 1.2) {
            findings.add(buildFinding(
                    jobId,
                    AnalysisDimensionEnum.HOOK,
                    PriorityEnum.P0,
                    "Target opening is slower or less direct than the reference set.",
                    "Target opening starts with more setup than the references.",
                    "Opening value appears later than the reference baseline.",
                    "Move the strongest information earlier in the first few seconds.",
                    "heuristic",
                    targetText,
                    referenceFeatures,
                    "If this is an atmospheric or story-led video, a delayed hook may be acceptable."
            ));
        }

        long targetActionWords = countKeywords(targetText, "then", "next", "finally", "step", "method");
        double referenceActionWords = referenceFeatures == null || referenceFeatures.isEmpty()
                ? 1.0
                : referenceFeatures.stream()
                .map(VideoFeature::getTextForDiagnosis)
                .map(this::normalize)
                .mapToLong(text -> countKeywords(text, "then", "next", "finally", "step", "method"))
                .average()
                .orElse(1.0);

        if (targetActionWords < referenceActionWords) {
            findings.add(buildFinding(
                    jobId,
                    AnalysisDimensionEnum.STRUCTURE_RHYTHM,
                    PriorityEnum.P1,
                    "Target structure has fewer visible transitions than the references.",
                    "The target uses fewer action transitions and section changes.",
                    "The reference videos change pace more often.",
                    "Use clearer sections such as problem -> demo -> result -> summary.",
                    "heuristic",
                    targetText,
                    referenceFeatures,
                    "If the video is intentionally minimalist, fewer transitions may be a style choice."
            ));
        }

        boolean targetHasValueSignal = containsAny(targetText, "result", "value", "solution", "method", "step", "tip", "advice");
        boolean referenceHasValueSignal = referenceFeatures != null
                && referenceFeatures.stream()
                .map(VideoFeature::getTextForDiagnosis)
                .map(this::normalize)
                .anyMatch(text -> containsAny(text, "result", "value", "solution", "method", "step", "tip", "advice"));

        if (!targetHasValueSignal || referenceHasValueSignal) {
            findings.add(buildFinding(
                    jobId,
                    AnalysisDimensionEnum.VALUE_DELIVERY,
                    PriorityEnum.P1,
                    "Target value delivery is not explicit enough compared with the references.",
                    "The target does not state the concrete payoff as early as the reference set.",
                    "Reference content more directly tells the viewer what they get.",
                    "State the payoff earlier and make the promised value more concrete.",
                    "heuristic",
                    targetText,
                    referenceFeatures,
                    "If this is an entertainment-only clip, the value may come from emotion or surprise instead of utility."
            ));
        }

        return findings;
    }

    private Finding buildFinding(String jobId,
                                 AnalysisDimensionEnum dimension,
                                 PriorityEnum priority,
                                 String observation,
                                 String differenceText,
                                 String hypothesisText,
                                 String suggestedAction,
                                 String source,
                                 String targetText,
                                 List<VideoFeature> references,
                                 String counterEvidence) {
        Finding finding = new Finding();
        finding.setId(UUID.randomUUID().toString());
        finding.setJobId(jobId);
        finding.setDimension(dimension);
        finding.setPriority(priority);
        finding.setStatus("normal");
        finding.setObservation(observation);
        finding.setTargetEvidence(new Evidence(List.of("00:00:00-00:00:05"), List.of(), List.of(clamp(targetText))));
        finding.setReferenceEvidence(new Evidence(List.of(), collectReferenceEvidence(references), List.of()));
        finding.setDifferenceText(differenceText);
        finding.setHypothesis(new Hypothesis(hypothesisText));
        finding.setConfidence(priority == PriorityEnum.P0 ? 0.86 : 0.72);
        finding.setSource(source);
        finding.setCounterEvidence(counterEvidence);
        finding.setSuggestedAction(suggestedAction);
        finding.setCreatedAt(LocalDateTime.now());
        finding.setUpdatedAt(LocalDateTime.now());
        return finding;
    }

    private List<String> collectReferenceEvidence(List<VideoFeature> references) {
        if (references == null || references.isEmpty()) {
            return List.of();
        }
        return references.stream()
                .limit(3)
                .map(ref -> clamp(normalize(ref.getTextForDiagnosis())))
                .toList();
    }

    private String normalize(String text) {
        return text == null ? "" : text.trim();
    }

    private boolean containsAny(String text, String... keywords) {
        for (String keyword : keywords) {
            if (text.contains(keyword)) {
                return true;
            }
        }
        return false;
    }

    private long countKeywords(String text, String... keywords) {
        long count = 0;
        for (String keyword : keywords) {
            if (text.contains(keyword)) {
                count++;
            }
        }
        return count;
    }

    private String clamp(String text) {
        if (text == null) {
            return "";
        }
        String normalized = text.replace('\n', ' ').replace('\r', ' ').trim();
        return normalized.length() <= 80 ? normalized : normalized.substring(0, 80) + "...";
    }
}
