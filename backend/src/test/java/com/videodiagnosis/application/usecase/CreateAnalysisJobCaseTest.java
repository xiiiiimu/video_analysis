package com.videodiagnosis.application.usecase;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.application.command.CreateAnalysisJobCommand;
import com.videodiagnosis.application.config.AgentJobProperties;
import com.videodiagnosis.application.view.AnalysisJobCreationResult;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.repository.AnalysisJobRepository;
import com.videodiagnosis.domain.repository.SkillDefinitionRepository;
import com.videodiagnosis.domain.repository.VideoAssetRepository;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * 两个相同的建任务请求同时到达：都查不到已有任务、都去插入，job_key 唯一索引只放进一个。
 * 输的那个不能报 500，而是返回赢家的任务（两次请求拿到同一个 jobId）。
 */
class CreateAnalysisJobCaseTest {

    private final AnalysisJobRepository jobs = mock(AnalysisJobRepository.class);
    private final VideoAssetRepository videos = mock(VideoAssetRepository.class);
    private final SkillDefinitionRepository skills = mock(SkillDefinitionRepository.class);
    private final CreateAnalysisJobCase useCase =
            new CreateAnalysisJobCase(jobs, videos, skills, new AgentJobProperties(), new ObjectMapper());

    private final CreateAnalysisJobCommand command = new CreateAnalysisJobCommand(
            "target", List.of("ref"), "标题", "", List.of(), List.of(), false, false, "", false, "");

    private static VideoAsset readyVideo(String id) {
        VideoAsset asset = new VideoAsset();
        asset.setId(id);
        asset.markProcessed();
        return asset;
    }

    @Test
    void losingConcurrentInsertReturnsTheExistingJob() {
        AnalysisJob winner = new AnalysisJob();
        winner.setId("job-from-other-request");
        when(videos.findById("target")).thenReturn(Optional.of(readyVideo("target")));
        when(videos.findAllByIds(anyList())).thenReturn(List.of(readyVideo("ref")));
        when(skills.findEnabled()).thenReturn(List.of());
        // 第一次查：还没有（对方尚未提交）；插入撞唯一索引；第二次查：对方已提交
        when(jobs.findByJobKey(anyString())).thenReturn(Optional.empty(), Optional.of(winner));
        when(jobs.save(any())).thenThrow(new DataIntegrityViolationException("uk_job_key"));

        AnalysisJobCreationResult result = useCase.execute(command);

        assertThat(result.created()).isFalse();
        assertThat(result.job().getId()).isEqualTo("job-from-other-request");
    }

    @Test
    void otherIntegrityErrorsStillSurface() {
        when(videos.findById("target")).thenReturn(Optional.of(readyVideo("target")));
        when(videos.findAllByIds(anyList())).thenReturn(List.of(readyVideo("ref")));
        when(skills.findEnabled()).thenReturn(List.of());
        // 冲突不是 job_key（回查仍然查不到）：原样抛出，不吞异常
        when(jobs.findByJobKey(anyString())).thenReturn(Optional.empty());
        when(jobs.save(any())).thenThrow(new DataIntegrityViolationException("other constraint"));

        assertThatThrownBy(() -> useCase.execute(command)).isInstanceOf(DataIntegrityViolationException.class);
    }
}
