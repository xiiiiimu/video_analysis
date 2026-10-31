package com.videodiagnosis.application.workflow;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.domain.repository.FindingRepository;
import com.videodiagnosis.domain.repository.VideoFeatureRepository;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.springframework.stereotype.Component;

import java.util.EnumSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * @deprecated 业务已迁移至 agent-service 异步链路（Python Harness + LangGraph 承担推理编排，
 * Java 侧由 {@link com.videodiagnosis.application.usecase.StartAgentDiagnosisCase} 触发、
 * {@link com.videodiagnosis.application.usecase.HandleAgentResultCase} 接收回调）。
 * 本类为历史 Java 内存同步编排（预处理 + 诊断 + 修订），仅保留用于比对参考，新业务请勿调用。
 */
@Deprecated
@Component
public class AnalysisJobWorkflow {

    private static final int MAX_RETRIES = 3;
    private static final Set<ErrorCode> RETRYABLE_ERROR_CODES = EnumSet.of(
            ErrorCode.PREPROCESS_FAILED,
            ErrorCode.ASR_FAILED,
            ErrorCode.MODEL_FAILED,
            ErrorCode.RESULT_BUILD_FAILED,
            ErrorCode.INTERNAL_ERROR
    );

    private final AnalysisJobRepository analysisJobRepository;
    private final PreprocessWorkflow preprocessWorkflow;
    private final DiagnosisWorkflow diagnosisWorkflow;
    private final RevisionPlanWorkflow revisionPlanWorkflow;
    private final FindingRepository findingRepository;
    private final VideoFeatureRepository videoFeatureRepository;

    public AnalysisJobWorkflow(AnalysisJobRepository analysisJobRepository,
                               PreprocessWorkflow preprocessWorkflow,
                               DiagnosisWorkflow diagnosisWorkflow,
                               RevisionPlanWorkflow revisionPlanWorkflow,
                               FindingRepository findingRepository,
                               VideoFeatureRepository videoFeatureRepository) {
        this.analysisJobRepository = analysisJobRepository;
        this.preprocessWorkflow = preprocessWorkflow;
        this.diagnosisWorkflow = diagnosisWorkflow;
        this.revisionPlanWorkflow = revisionPlanWorkflow;
        this.findingRepository = findingRepository;
        this.videoFeatureRepository = videoFeatureRepository;
    }

    public void execute(String jobId) {
        AnalysisJob job = analysisJobRepository.findById(jobId)
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.JOB_NOT_FOUND, "Analysis job not found: " + jobId));

        try {
            runWithRetry(job);
        } catch (VideoDiagnosisException ex) {
            job.markFailed(ex.getErrorCode().getCode(), ex.getMessage());
            analysisJobRepository.save(job);
        } catch (Exception ex) {
            job.markFailed(ErrorCode.INTERNAL_ERROR.getCode(), ex.getMessage());
            analysisJobRepository.save(job);
        }
    }

    private void runWithRetry(AnalysisJob job) {
        RuntimeException lastFailure = null;
        for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
            try {
                executeOnce(job);
                return;
            } catch (VideoDiagnosisException ex) {
                if (!isRetryable(ex) || attempt == MAX_RETRIES) {
                    throw ex;
                }
                lastFailure = ex;
                sleepQuietly(attempt);
            } catch (RuntimeException ex) {
                if (attempt == MAX_RETRIES) {
                    throw ex;
                }
                lastFailure = ex;
                sleepQuietly(attempt);
            }
        }
        if (lastFailure != null) {
            throw lastFailure;
        }
    }

    private void executeOnce(AnalysisJob job) {
        job.markPreprocessing();
        analysisJobRepository.save(job);

        List<VideoFeature> features = preprocessWorkflow.execute(job);

        job.markAnalyzing();
        analysisJobRepository.save(job);

        VideoFeature targetFeature = features.stream()
                .filter(feature -> feature.getVideoAssetId().equals(job.getTargetVideoId()))
                .findFirst()
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.PREPROCESS_FAILED, "Target feature missing."));

        List<VideoFeature> referenceFeatures = features.stream()
                .filter(feature -> !feature.getVideoAssetId().equals(job.getTargetVideoId()))
                .toList();

        List<Finding> findings = diagnosisWorkflow.execute(job, targetFeature, referenceFeatures);
        findingRepository.saveAll(findings);
        revisionPlanWorkflow.execute(findings);

        job.markCompleted();
        analysisJobRepository.save(job);
    }

    private boolean isRetryable(VideoDiagnosisException exception) {
        return exception.getErrorCode() != null && RETRYABLE_ERROR_CODES.contains(exception.getErrorCode());
    }

    private void sleepQuietly(int attempt) {
        try {
            TimeUnit.MILLISECONDS.sleep(200L * attempt);
        } catch (InterruptedException interruptedException) {
            Thread.currentThread().interrupt();
        }
    }
}
