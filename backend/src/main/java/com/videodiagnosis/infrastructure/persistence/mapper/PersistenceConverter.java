package com.videodiagnosis.infrastructure.persistence.mapper;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.CoverageState;
import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.entity.SkillDefinition;
import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.valueobject.Evidence;
import com.videodiagnosis.domain.valueobject.Hypothesis;
import com.videodiagnosis.domain.valueobject.VideoMeta;
import com.videodiagnosis.infrastructure.persistence.jpa.entity.AnalysisJobJpaEntity;
import com.videodiagnosis.infrastructure.persistence.jpa.entity.CoverageStateJpaEntity;
import com.videodiagnosis.infrastructure.persistence.jpa.entity.FindingJpaEntity;
import com.videodiagnosis.infrastructure.persistence.jpa.entity.SkillDefinitionJpaEntity;
import com.videodiagnosis.infrastructure.persistence.jpa.entity.VideoAssetJpaEntity;
import com.videodiagnosis.infrastructure.persistence.jpa.entity.VideoFeatureJpaEntity;
import com.videodiagnosis.types.enums.AnalysisDimensionEnum;
import com.videodiagnosis.types.enums.JobStatusEnum;
import com.videodiagnosis.types.enums.PriorityEnum;
import com.videodiagnosis.types.enums.VideoStatusEnum;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Component
public class PersistenceConverter {

    private final PersistenceMapper persistenceMapper;

    public PersistenceConverter(PersistenceMapper persistenceMapper) {
        this.persistenceMapper = persistenceMapper;
    }

    public AnalysisJob toDomain(AnalysisJobJpaEntity entity) {
        if (entity == null) {
            return null;
        }
        AnalysisJob job = new AnalysisJob();
        job.setId(entity.getId());
        job.setJobKey(entity.getJobKey());
        job.setTargetVideoId(entity.getTargetVideoId());
        job.setReferenceVideoIds(persistenceMapper.readList(entity.getReferenceVideoIdsJson()));
        job.setStatus(entity.getStatus() == null ? null : JobStatusEnum.valueOf(entity.getStatus()));
        job.setProgress(entity.getProgress());
        job.setCurrentStage(entity.getCurrentStage());
        job.setInputSnapshotJson(entity.getInputSnapshotJson());
        job.setSkillVersionSnapshotJson(entity.getSkillVersionSnapshotJson());
        job.setErrorCode(entity.getErrorCode());
        job.setErrorMessage(entity.getErrorMessage());
        job.setVersion(entity.getVersion());
        job.setRetryCount(entity.getRetryCount());
        job.setMaxRetryCount(entity.getMaxRetryCount() <= 0 ? 3 : entity.getMaxRetryCount());
        job.setNextRetryAt(entity.getNextRetryAt());
        job.setLastError(entity.getLastError());
        job.setCurrentAgentRunId(entity.getCurrentAgentRunId());
        job.setAgentStartedAt(entity.getAgentStartedAt());
        job.setAgentTimeoutAt(entity.getAgentTimeoutAt());
        job.setLastProcessedAgentRunId(entity.getLastProcessedAgentRunId());
        job.setLastResultVersion(entity.getLastResultVersion());
        job.setCreatedAt(entity.getCreatedAt());
        job.setUpdatedAt(entity.getUpdatedAt());
        job.setStartedAt(entity.getStartedAt());
        job.setFinishedAt(entity.getFinishedAt());
        return job;
    }

    public AnalysisJobJpaEntity toEntity(AnalysisJob job) {
        AnalysisJobJpaEntity entity = new AnalysisJobJpaEntity();
        entity.setId(job.getId());
        entity.setJobKey(job.getJobKey());
        entity.setTargetVideoId(job.getTargetVideoId());
        entity.setReferenceVideoIdsJson(persistenceMapper.writeList(job.getReferenceVideoIds()));
        entity.setStatus(job.getStatus() == null ? null : job.getStatus().name());
        entity.setProgress(job.getProgress());
        entity.setCurrentStage(job.getCurrentStage());
        entity.setInputSnapshotJson(job.getInputSnapshotJson());
        entity.setSkillVersionSnapshotJson(job.getSkillVersionSnapshotJson());
        entity.setErrorCode(job.getErrorCode());
        entity.setErrorMessage(job.getErrorMessage());
        entity.setVersion(job.getVersion());
        entity.setRetryCount(job.getRetryCount());
        entity.setMaxRetryCount(job.getMaxRetryCount());
        entity.setNextRetryAt(job.getNextRetryAt());
        entity.setLastError(job.getLastError());
        entity.setCurrentAgentRunId(job.getCurrentAgentRunId());
        entity.setAgentStartedAt(job.getAgentStartedAt());
        entity.setAgentTimeoutAt(job.getAgentTimeoutAt());
        entity.setLastProcessedAgentRunId(job.getLastProcessedAgentRunId());
        entity.setLastResultVersion(job.getLastResultVersion());
        entity.setCreatedAt(job.getCreatedAt());
        entity.setUpdatedAt(job.getUpdatedAt());
        entity.setStartedAt(job.getStartedAt());
        entity.setFinishedAt(job.getFinishedAt());
        return entity;
    }

    public VideoAsset toDomain(VideoAssetJpaEntity entity) {
        if (entity == null) {
            return null;
        }
        VideoAsset asset = new VideoAsset();
        asset.setId(entity.getId());
        asset.setOwnerId(entity.getOwnerId());
        asset.setRole(entity.getRole());
        asset.setTitle(entity.getTitle());
        asset.setDescription(entity.getDescription());
        asset.setCoverUrl(entity.getCoverUrl());
        asset.setFileUrl(entity.getFileUrl());
        asset.setFileSize(entity.getFileSize());
        asset.setDurationMs(entity.getDurationMs());
        asset.setMimeType(entity.getMimeType());
        asset.setStatus(entity.getStatus() == null ? null : VideoStatusEnum.valueOf(entity.getStatus()));
        asset.setMeta(entity.getMimeType() == null ? null : new VideoMeta(entity.getDurationMs(), 0, 0, 0, entity.getMimeType()));
        asset.setCreatedAt(entity.getCreatedAt());
        asset.setUpdatedAt(entity.getUpdatedAt());
        return asset;
    }

    public VideoAssetJpaEntity toEntity(VideoAsset asset) {
        VideoAssetJpaEntity entity = new VideoAssetJpaEntity();
        entity.setId(asset.getId());
        entity.setOwnerId(asset.getOwnerId());
        entity.setRole(asset.getRole());
        entity.setTitle(asset.getTitle());
        entity.setDescription(asset.getDescription());
        entity.setCoverUrl(asset.getCoverUrl());
        entity.setFileUrl(asset.getFileUrl());
        entity.setFileSize(asset.getFileSize());
        entity.setDurationMs(asset.getDurationMs());
        entity.setMimeType(asset.getMimeType());
        entity.setStatus(asset.getStatus() == null ? null : asset.getStatus().name());
        entity.setCreatedAt(asset.getCreatedAt());
        entity.setUpdatedAt(asset.getUpdatedAt());
        return entity;
    }

    public VideoFeature toDomain(VideoFeatureJpaEntity entity) {
        if (entity == null) {
            return null;
        }
        VideoFeature feature = new VideoFeature();
        feature.setId(entity.getId());
        feature.setVideoAssetId(entity.getVideoAssetId());
        feature.setJobId(entity.getJobId());
        feature.setTranscriptText(entity.getTranscriptText());
        feature.setKeyframes(persistenceMapper.readList(entity.getKeyframesJson()));
        feature.setSceneJson(entity.getSceneJson());
        feature.setOcrJson(entity.getOcrJson());
        feature.setTimelineJson(entity.getTimelineJson());
        feature.setMeta(persistenceMapper.readVideoMeta(entity.getMetaJson()));
        feature.setFeatureVersion(entity.getFeatureVersion());
        feature.setCreatedAt(entity.getCreatedAt());
        feature.setUpdatedAt(entity.getUpdatedAt());
        return feature;
    }

    public VideoFeatureJpaEntity toEntity(VideoFeature feature) {
        VideoFeatureJpaEntity entity = new VideoFeatureJpaEntity();
        entity.setId(feature.getId());
        entity.setVideoAssetId(feature.getVideoAssetId());
        entity.setJobId(feature.getJobId());
        entity.setTranscriptText(feature.getTranscriptText());
        entity.setKeyframesJson(persistenceMapper.writeList(feature.getKeyframes()));
        entity.setSceneJson(feature.getSceneJson());
        entity.setOcrJson(feature.getOcrJson());
        entity.setTimelineJson(feature.getTimelineJson());
        entity.setMetaJson(persistenceMapper.writeVideoMeta(feature.getMeta()));
        entity.setFeatureVersion(feature.getFeatureVersion());
        entity.setCreatedAt(feature.getCreatedAt());
        entity.setUpdatedAt(feature.getUpdatedAt());
        return entity;
    }

    public SkillDefinition toDomain(SkillDefinitionJpaEntity entity) {
        if (entity == null) {
            return null;
        }
        SkillDefinition definition = new SkillDefinition();
        definition.setId(entity.getId());
        definition.setSkillKey(entity.getSkillKey());
        definition.setVersion(entity.getVersion());
        definition.setName(entity.getName());
        definition.setCoverageDimension(entity.getCoverageDimension() == null ? null : AnalysisDimensionEnum.valueOf(entity.getCoverageDimension()));
        definition.setToolAllowList(persistenceMapper.readList(entity.getToolAllowListJson()));
        definition.setEnabled(entity.isEnabled());
        definition.setCreatedAt(entity.getCreatedAt());
        definition.setUpdatedAt(entity.getUpdatedAt());
        return definition;
    }

    public SkillDefinitionJpaEntity toEntity(SkillDefinition definition) {
        SkillDefinitionJpaEntity entity = new SkillDefinitionJpaEntity();
        entity.setId(definition.getId());
        entity.setSkillKey(definition.getSkillKey());
        entity.setVersion(definition.getVersion());
        entity.setName(definition.getName());
        entity.setCoverageDimension(definition.getCoverageDimension() == null ? null : definition.getCoverageDimension().name());
        entity.setToolAllowListJson(persistenceMapper.writeList(definition.getToolAllowList()));
        entity.setEnabled(definition.isEnabled());
        entity.setCreatedAt(definition.getCreatedAt());
        entity.setUpdatedAt(definition.getUpdatedAt());
        return entity;
    }

    public Finding toDomain(FindingJpaEntity entity) {
        if (entity == null) {
            return null;
        }
        Finding finding = new Finding();
        finding.setId(entity.getId());
        finding.setJobId(entity.getJobId());
        finding.setDimension(entity.getDimension() == null ? null : AnalysisDimensionEnum.valueOf(entity.getDimension()));
        finding.setPriority(entity.getPriority() == null ? null : PriorityEnum.valueOf(entity.getPriority()));
        finding.setStatus(entity.getStatus());
        finding.setObservation(entity.getObservation());
        finding.setTargetEvidence(persistenceMapper.readObject(entity.getTargetEvidenceJson(), Evidence.class));
        finding.setReferenceEvidence(persistenceMapper.readObject(entity.getReferenceEvidenceJson(), Evidence.class));
        finding.setDifferenceText(entity.getDifferenceText());
        finding.setHypothesis(entity.getHypothesisText() == null ? null : new Hypothesis(entity.getHypothesisText()));
        finding.setConfidence(entity.getConfidence());
        finding.setSource(entity.getSource());
        finding.setCounterEvidence(entity.getCounterEvidence());
        finding.setSuggestedAction(entity.getSuggestedAction());
        finding.setCreatedAt(entity.getCreatedAt());
        finding.setUpdatedAt(entity.getUpdatedAt());
        return finding;
    }

    public FindingJpaEntity toEntity(Finding finding) {
        FindingJpaEntity entity = new FindingJpaEntity();
        entity.setId(finding.getId());
        entity.setJobId(finding.getJobId());
        entity.setDimension(finding.getDimension() == null ? null : finding.getDimension().name());
        entity.setPriority(finding.getPriority() == null ? null : finding.getPriority().name());
        entity.setStatus(finding.getStatus());
        entity.setObservation(finding.getObservation());
        entity.setTargetEvidenceJson(persistenceMapper.writeObject(finding.getTargetEvidence()));
        entity.setReferenceEvidenceJson(persistenceMapper.writeObject(finding.getReferenceEvidence()));
        entity.setDifferenceText(finding.getDifferenceText());
        entity.setHypothesisText(finding.getHypothesis() == null ? null : finding.getHypothesis().text());
        entity.setConfidence(finding.getConfidence());
        entity.setSource(finding.getSource());
        entity.setCounterEvidence(finding.getCounterEvidence());
        entity.setSuggestedAction(finding.getSuggestedAction());
        entity.setCreatedAt(finding.getCreatedAt());
        entity.setUpdatedAt(finding.getUpdatedAt());
        return entity;
    }

    public CoverageState toDomain(CoverageStateJpaEntity entity) {
        if (entity == null) {
            return null;
        }
        CoverageState coverageState = new CoverageState();
        coverageState.setId(entity.getId());
        coverageState.setJobId(entity.getJobId());
        coverageState.setDimension(entity.getDimension() == null ? null : AnalysisDimensionEnum.valueOf(entity.getDimension()));
        coverageState.setState(entity.getState());
        coverageState.setReason(entity.getReason());
        coverageState.setCreatedAt(entity.getCreatedAt());
        coverageState.setUpdatedAt(entity.getUpdatedAt());
        return coverageState;
    }

    public CoverageStateJpaEntity toEntity(CoverageState coverageState) {
        CoverageStateJpaEntity entity = new CoverageStateJpaEntity();
        entity.setId(coverageState.getId());
        entity.setJobId(coverageState.getJobId());
        entity.setDimension(coverageState.getDimension() == null ? null : coverageState.getDimension().name());
        entity.setState(coverageState.getState());
        entity.setReason(coverageState.getReason());
        entity.setCreatedAt(coverageState.getCreatedAt());
        entity.setUpdatedAt(coverageState.getUpdatedAt());
        return entity;
    }

    public String newId() {
        return UUID.randomUUID().toString();
    }

    public LocalDateTime now() {
        return LocalDateTime.now();
    }
}
