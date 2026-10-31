package com.videodiagnosis.application.usecase;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.application.command.CreateAnalysisJobCommand;
import com.videodiagnosis.application.config.AgentJobProperties;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.SkillDefinition;
import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.domain.repository.SkillDefinitionRepository;
import com.videodiagnosis.domain.repository.VideoAssetRepository;
import com.videodiagnosis.application.view.AnalysisJobCreationResult;
import com.videodiagnosis.types.common.CommonConstants;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import com.videodiagnosis.types.enums.JobStatusEnum;
import com.videodiagnosis.types.enums.VideoStatusEnum;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Component
public class CreateAnalysisJobCase {

    private final AnalysisJobRepository analysisJobRepository;
    private final VideoAssetRepository videoAssetRepository;
    private final SkillDefinitionRepository skillDefinitionRepository;
    private final AgentJobProperties agentJobProperties;
    private final ObjectMapper objectMapper;

    public CreateAnalysisJobCase(AnalysisJobRepository analysisJobRepository,
                                 VideoAssetRepository videoAssetRepository,
                                 SkillDefinitionRepository skillDefinitionRepository,
                                 AgentJobProperties agentJobProperties,
                                 ObjectMapper objectMapper) {
        this.analysisJobRepository = analysisJobRepository;
        this.videoAssetRepository = videoAssetRepository;
        this.skillDefinitionRepository = skillDefinitionRepository;
        this.agentJobProperties = agentJobProperties;
        this.objectMapper = objectMapper;
    }

    public AnalysisJobCreationResult execute(CreateAnalysisJobCommand command) {
        VideoAsset target = videoAssetRepository.findById(command.targetVideoId())
                .orElseThrow(() -> new VideoDiagnosisException(ErrorCode.VIDEO_NOT_FOUND, "Target video not found: " + command.targetVideoId()));
        ensureVideoReady(target, "Target");

        List<VideoAsset> references = videoAssetRepository.findAllByIds(command.referenceVideoIds());
        if (references.size() != command.referenceVideoIds().size()) {
            throw new VideoDiagnosisException(ErrorCode.REFERENCE_VIDEO_MISSING, "One or more reference videos are missing.");
        }
        references.forEach(reference -> ensureVideoReady(reference, "Reference"));

        String jobKey = buildJobKey(command);
        AnalysisJob existing = analysisJobRepository.findByJobKey(jobKey).orElse(null);
        if (existing != null) {
            return new AnalysisJobCreationResult(existing, false);
        }
        try {
            return new AnalysisJobCreationResult(createJob(command, target.getId(), jobKey), true);
        } catch (DataIntegrityViolationException ex) {
            // 先查后插不是原子的：两个相同请求（重复点击、网关重试）同时走到这里，都查不到，都去插入。
            // job_key 唯一索引只放进一个，另一个原来直接抛 500；现在回查并返回已存在的任务，两次请求拿到同一个 jobId。
            AnalysisJob winner = analysisJobRepository.findByJobKey(jobKey).orElseThrow(() -> ex);
            return new AnalysisJobCreationResult(winner, false);
        }
    }

    private AnalysisJob createJob(CreateAnalysisJobCommand command, String targetVideoId, String jobKey) {
        AnalysisJob job = new AnalysisJob();
        job.setId(UUID.randomUUID().toString());
        job.setJobKey(jobKey);
        job.setTargetVideoId(targetVideoId);
        job.setReferenceVideoIds(command.referenceVideoIds());
        job.setStatus(JobStatusEnum.CREATED);
        job.setProgress(0);
        job.setCurrentStage("CREATED");
        job.setMaxRetryCount(agentJobProperties.getMaxRetryCount());
        job.setNextRetryAt(LocalDateTime.now());
        job.setInputSnapshotJson(buildInputSnapshot(command));
        job.setSkillVersionSnapshotJson(buildSkillSnapshot());
        job.setCreatedAt(LocalDateTime.now());
        job.setUpdatedAt(LocalDateTime.now());
        job.waitForAgent(LocalDateTime.now());
        analysisJobRepository.save(job);
        return job;
    }

    private String buildJobKey(CreateAnalysisJobCommand command) {
        String raw = String.join("|",
                safeText(command.targetVideoId()),
                command.referenceVideoIds() == null ? "" : String.join(",", command.referenceVideoIds()),
                safeText(command.targetTitle()),
                safeText(command.targetDescription()),
                command.referenceTitles() == null ? "" : String.join(",", command.referenceTitles()),
                command.referenceDescriptions() == null ? "" : String.join(",", command.referenceDescriptions()),
                String.valueOf(command.enableCoverAnalysis()),
                String.valueOf(command.enablePerformanceAnalysis()),
                // 评分标准不同就是不同的任务（同样两个视频、换一套标准要重新分析）
                sha256(safeText(command.criteriaText())),
                String.valueOf(command.supplementaryAnalysis()),
                safeText(command.category())
        );
        return sha256(raw);
    }

    private String buildInputSnapshot(CreateAnalysisJobCommand command) {
        // 改用 Jackson 序列化：评分标准是多行文本，原来手拼 JSON 只转义了引号和反斜杠，换行会产生非法 JSON
        Map<String, Object> snapshot = new LinkedHashMap<>();
        snapshot.put("targetVideoId", safeText(command.targetVideoId()));
        snapshot.put("referenceVideoIds", command.referenceVideoIds() == null ? List.of() : command.referenceVideoIds());
        snapshot.put("targetTitle", safeText(command.targetTitle()));
        snapshot.put("targetDescription", safeText(command.targetDescription()));
        snapshot.put("referenceTitles", command.referenceTitles() == null ? List.of() : command.referenceTitles());
        snapshot.put("referenceDescriptions", command.referenceDescriptions() == null ? List.of() : command.referenceDescriptions());
        snapshot.put("enableCoverAnalysis", command.enableCoverAnalysis());
        snapshot.put("enablePerformanceAnalysis", command.enablePerformanceAnalysis());
        snapshot.put("criteriaText", safeText(command.criteriaText()));
        snapshot.put("supplementaryAnalysis", command.supplementaryAnalysis());
        snapshot.put("category", safeText(command.category()));
        try {
            return objectMapper.writeValueAsString(snapshot);
        } catch (JsonProcessingException ex) {
            throw new IllegalStateException("Unable to serialize input snapshot", ex);
        }
    }

    private String buildSkillSnapshot() {
        return skillDefinitionRepository.findEnabled().stream()
                .map(SkillDefinition::getSkillKey)
                .reduce((left, right) -> left + "," + right)
                .orElse(CommonConstants.DEFAULT_SKILL_VERSION);
    }

    private void ensureVideoReady(VideoAsset asset, String label) {
        if (asset.getStatus() == null) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, label + " video is not ready: " + asset.getId());
        }
        if (asset.getStatus() != VideoStatusEnum.READY && asset.getStatus() != VideoStatusEnum.PROCESSED) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, label + " video is not ready: " + asset.getId());
        }
    }

    private String safeText(String value) {
        return value == null ? "" : value.trim();
    }

    private String sha256(String value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(value.getBytes(StandardCharsets.UTF_8));
            StringBuilder builder = new StringBuilder();
            for (byte b : hash) {
                builder.append(String.format("%02x", b));
            }
            return builder.toString();
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException("Unable to compute job key", ex);
        }
    }
}
