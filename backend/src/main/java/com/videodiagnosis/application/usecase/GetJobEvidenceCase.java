package com.videodiagnosis.application.usecase;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.domain.repository.VideoFeatureRepository;
import com.videodiagnosis.interfaces.response.InternalJobEvidenceResponse;
import com.videodiagnosis.interfaces.response.InternalVideoEvidenceResponse;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * 为 agent-service 提供视频帧/转写等证据包（权威数据来自 MySQL）。
 */
@Component
public class GetJobEvidenceCase {

    private final AnalysisJobRepository analysisJobRepository;
    private final VideoFeatureRepository videoFeatureRepository;

    public GetJobEvidenceCase(AnalysisJobRepository analysisJobRepository,
                              VideoFeatureRepository videoFeatureRepository) {
        this.analysisJobRepository = analysisJobRepository;
        this.videoFeatureRepository = videoFeatureRepository;
    }

    public InternalJobEvidenceResponse execute(String jobId) {
        AnalysisJob job = analysisJobRepository.findById(jobId)
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.JOB_NOT_FOUND, "Analysis job not found: " + jobId));

        List<VideoFeature> features = videoFeatureRepository.findByJobId(jobId);
        Map<String, VideoFeature> byVideoId = features.stream()
                .collect(Collectors.toMap(VideoFeature::getVideoAssetId, Function.identity(), (left, right) -> left));

        VideoFeature targetFeature = resolveFeature(byVideoId, job.getTargetVideoId());
        List<InternalVideoEvidenceResponse> references = new ArrayList<>();
        if (job.getReferenceVideoIds() != null) {
            for (String referenceId : job.getReferenceVideoIds()) {
                VideoFeature referenceFeature = resolveFeature(byVideoId, referenceId);
                if (referenceFeature != null) {
                    references.add(toEvidence(referenceFeature));
                }
            }
        }

        return new InternalJobEvidenceResponse(
                job.getId(),
                job.getTargetVideoId(),
                targetFeature == null ? emptyEvidence(job.getTargetVideoId()) : toEvidence(targetFeature),
                references
        );
    }

    /**
     * Agent 链路里，特征是在上传视频时提取的（jobId = AUTO_FRAME），并不以任务 ID 保存，
     * 只按 jobId 查会拿到空证据。先按任务查，查不到再按视频取它的特征。
     */
    private VideoFeature resolveFeature(Map<String, VideoFeature> byJob, String videoAssetId) {
        VideoFeature feature = byJob.get(videoAssetId);
        if (feature != null) {
            return feature;
        }
        return videoFeatureRepository.findByVideoAssetId(videoAssetId).orElse(null);
    }

    private InternalVideoEvidenceResponse toEvidence(VideoFeature feature) {
        return new InternalVideoEvidenceResponse(
                feature.getVideoAssetId(),
                feature.getTranscriptText(),
                feature.getKeyframes() == null ? List.of() : feature.getKeyframes(),
                feature.getSceneJson(),
                feature.getOcrJson(),
                feature.getTimelineJson()
        );
    }

    private InternalVideoEvidenceResponse emptyEvidence(String videoAssetId) {
        return new InternalVideoEvidenceResponse(videoAssetId, "", List.of(), null, null, null);
    }
}
