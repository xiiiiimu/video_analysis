package com.videodiagnosis.interfaces.assembler;

import com.videodiagnosis.application.view.AnalysisResultView;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.CoverageState;
import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.interfaces.response.AnalysisJobDetailResponse;
import com.videodiagnosis.interfaces.response.AnalysisJobResultResponse;
import com.videodiagnosis.interfaces.response.AnalysisRecommendationResponse;
import com.videodiagnosis.interfaces.response.CoverageStateResponse;
import com.videodiagnosis.interfaces.response.CreateAnalysisJobResponse;
import com.videodiagnosis.interfaces.response.FindingResponse;

import java.util.List;

public class AnalysisJobAssembler {

    public CreateAnalysisJobResponse toCreateResponse(AnalysisJob job) {
        return new CreateAnalysisJobResponse(job.getId(), String.valueOf(job.getStatus()));
    }

    public AnalysisJobDetailResponse toDetailResponse(AnalysisJob job) {
        return new AnalysisJobDetailResponse(
                job.getId(),
                String.valueOf(job.getStatus()),
                job.getProgress(),
                job.getCurrentStage(),
                job.getErrorMessage(),
                job.getStartedAt(),
                job.getFinishedAt()
        );
    }

    public AnalysisJobResultResponse toResultResponse(AnalysisResultView view) {
        List<FindingResponse> findings = view.findings().stream().map(this::toFindingResponse).toList();
        List<AnalysisRecommendationResponse> recommendations = view.findings().stream()
                .map(this::toRecommendationResponse)
                .toList();
        List<CoverageStateResponse> coverageStates = view.coverageStates().stream().map(this::toCoverageStateResponse).toList();
        return new AnalysisJobResultResponse(
                view.job().getId(),
                String.valueOf(view.job().getStatus()),
                view.coreDimensions(),
                findings,
                recommendations,
                coverageStates,
                view.missingInputs(),
                view.revisionPlan()
        );
    }

    private FindingResponse toFindingResponse(Finding finding) {
        return new FindingResponse(
                String.valueOf(finding.getDimension()),
                String.valueOf(finding.getPriority()),
                finding.getObservation(),
                finding.getTargetEvidence() == null ? List.of() : finding.getTargetEvidence().target(),
                finding.getReferenceEvidence() == null ? List.of() : finding.getReferenceEvidence().reference(),
                finding.getDifferenceText(),
                finding.getHypothesis() == null ? null : finding.getHypothesis().text(),
                finding.getConfidence(),
                finding.getSource(),
                finding.getCounterEvidence(),
                finding.getSuggestedAction()
        );
    }

    private CoverageStateResponse toCoverageStateResponse(CoverageState coverageState) {
        return new CoverageStateResponse(
                String.valueOf(coverageState.getDimension()),
                coverageState.getState(),
                coverageState.getReason()
        );
    }

    private AnalysisRecommendationResponse toRecommendationResponse(Finding finding) {
        String title = finding.getObservation() == null || finding.getObservation().isBlank()
                ? String.valueOf(finding.getDimension())
                : finding.getObservation();
        return new AnalysisRecommendationResponse(
                String.valueOf(finding.getDimension()),
                String.valueOf(finding.getPriority()),
                title,
                finding.getSuggestedAction(),
                finding.getConfidence()
        );
    }
}

