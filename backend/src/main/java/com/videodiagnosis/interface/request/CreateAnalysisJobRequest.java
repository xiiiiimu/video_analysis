package com.videodiagnosis.interfaces.request;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.List;

public record CreateAnalysisJobRequest(
        @NotBlank String targetVideoId,
        @NotEmpty List<@NotBlank String> referenceVideoIds,
        String targetTitle,
        String targetDescription,
        List<String> referenceTitles,
        List<String> referenceDescriptions,
        boolean enableCoverAnalysis,
        boolean enablePerformanceAnalysis,
        // 用户自定义评分标准（任意格式的纯文本，前端读 txt 后放这里）；为空时只用内置评分点
        @Size(max = CreateAnalysisJobRequest.MAX_CRITERIA_CHARS) String criteriaText,
        // 额外跑一次整体补充分析（不管标准是否属于三个专家）；默认只处理三个专家之外的标准
        boolean supplementaryAnalysis,
        // 视频品类（例如"知识教程"）：知识库里标了同一品类的私有评分点只对这类任务生效；为空时只用通用评分点
        @Size(max = 50) String category
) {
    public static final int MAX_CRITERIA_CHARS = 20000;
}

