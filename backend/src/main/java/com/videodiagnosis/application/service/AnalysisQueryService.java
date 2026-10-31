package com.videodiagnosis.application.service;

import com.videodiagnosis.application.usecase.BuildResultCase;
import com.videodiagnosis.application.view.AnalysisResultView;
import com.videodiagnosis.application.view.AnalysisProgressSnapshot;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.domain.repository.VideoAssetRepository;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.springframework.stereotype.Service;

@Service
public class AnalysisQueryService {

    private final AnalysisJobRepository analysisJobRepository;
    private final VideoAssetRepository videoAssetRepository;
    private final BuildResultCase buildResultCase;
    private final AnalysisProgressService analysisProgressService;

    public AnalysisQueryService(AnalysisJobRepository analysisJobRepository,
                                VideoAssetRepository videoAssetRepository,
                                BuildResultCase buildResultCase,
                                AnalysisProgressService analysisProgressService) {
        this.analysisJobRepository = analysisJobRepository;
        this.videoAssetRepository = videoAssetRepository;
        this.buildResultCase = buildResultCase;
        this.analysisProgressService = analysisProgressService;
    }

    public AnalysisJob getJob(String jobId) {
        AnalysisJob job = analysisJobRepository.findById(jobId)
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.JOB_NOT_FOUND, "Analysis job not found: " + jobId));
        analysisProgressService.getProgress(jobId).ifPresent(snapshot -> applyProgressSnapshot(job, snapshot));
        return job;
    }

    public AnalysisResultView getResult(String jobId) {
        return buildResultCase.execute(jobId);
    }

    public VideoAsset getVideo(String videoId) {
        return videoAssetRepository.findById(videoId)
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.VIDEO_NOT_FOUND, "Video not found: " + videoId));
    }

    private void applyProgressSnapshot(AnalysisJob job, AnalysisProgressSnapshot snapshot) {
        job.setProgress(snapshot.progress());
        job.setCurrentStage(snapshot.stage());
    }
}
