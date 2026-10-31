package com.videodiagnosis.application.usecase;

import com.videodiagnosis.application.view.AnalysisResultView;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.CoverageState;
import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.domain.repository.CoverageStateRepository;
import com.videodiagnosis.domain.repository.FindingRepository;
import com.videodiagnosis.domain.repository.VideoAssetRepository;
import com.videodiagnosis.domain.repository.VideoFeatureRepository;
import com.videodiagnosis.infrastructure.client.ModelClientAdapter;
import com.videodiagnosis.domain.service.FindingRankDomainService;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import com.videodiagnosis.types.enums.AnalysisDimensionEnum;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class BuildResultCase {

    private final AnalysisJobRepository analysisJobRepository;
    private final FindingRepository findingRepository;
    private final CoverageStateRepository coverageStateRepository;
    private final VideoAssetRepository videoAssetRepository;
    private final VideoFeatureRepository videoFeatureRepository;
    private final FindingRankDomainService findingRankDomainService;
    private final ModelClientAdapter modelClientAdapter;

    public BuildResultCase(AnalysisJobRepository analysisJobRepository,
                           FindingRepository findingRepository,
                           CoverageStateRepository coverageStateRepository,
                           VideoAssetRepository videoAssetRepository,
                           VideoFeatureRepository videoFeatureRepository,
                           FindingRankDomainService findingRankDomainService,
                           ModelClientAdapter modelClientAdapter) {
        this.analysisJobRepository = analysisJobRepository;
        this.findingRepository = findingRepository;
        this.coverageStateRepository = coverageStateRepository;
        this.videoAssetRepository = videoAssetRepository;
        this.videoFeatureRepository = videoFeatureRepository;
        this.findingRankDomainService = findingRankDomainService;
        this.modelClientAdapter = modelClientAdapter;
    }

    public AnalysisResultView execute(String jobId) {
        AnalysisJob job = analysisJobRepository.findById(jobId)
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.JOB_NOT_FOUND, "Analysis job not found: " + jobId));
        List<Finding> findings = findingRankDomainService.rankAndLimit(findingRepository.findByJobId(jobId), 3);
        List<CoverageState> coverageStates = coverageStateRepository.findByJobId(jobId);
        List<String> missingInputs = buildMissingInputs(job);
        List<String> revisionPlan = buildRevisionPlan(job, findings);
        return new AnalysisResultView(job, buildCoreDimensions(), findings, coverageStates, missingInputs, revisionPlan);
    }

    private List<String> buildRevisionPlan(AnalysisJob job, List<Finding> findings) {
        if (findings != null && !findings.isEmpty()) {
            return List.of(modelClientAdapter.summarizeFindings(findings));
        }
        String snapshot = job.getSkillVersionSnapshotJson();
        if (snapshot != null && snapshot.startsWith("[")) {
            return List.of(snapshot);
        }
        return List.of("No core issue was found.");
    }

    private List<String> buildCoreDimensions() {
        return List.of(
                AnalysisDimensionEnum.HOOK.name(),
                AnalysisDimensionEnum.STRUCTURE_RHYTHM.name(),
                AnalysisDimensionEnum.VALUE_DELIVERY.name()
        );
    }

    private List<String> buildMissingInputs(AnalysisJob job) {
        List<String> missingInputs = new ArrayList<>();
        VideoAsset target = videoAssetRepository.findById(job.getTargetVideoId()).orElse(null);
        if (target == null || target.getFileUrl() == null || target.getFileUrl().isBlank()) {
            missingInputs.add("target_video");
        }
        // Agent 链路的特征在上传视频时提取（jobId=AUTO_FRAME），按任务查不到时按目标视频查，
        // 否则结果接口会误报 missingInputs=video_feature
        List<VideoFeature> features = videoFeatureRepository.findByJobId(job.getId());
        boolean hasFeature = !features.isEmpty()
                || videoFeatureRepository.findByVideoAssetId(job.getTargetVideoId()).isPresent();
        if (!hasFeature) {
            missingInputs.add("video_feature");
        }
        return missingInputs;
    }
}
