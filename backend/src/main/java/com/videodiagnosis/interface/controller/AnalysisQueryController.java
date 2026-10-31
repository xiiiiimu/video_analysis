package com.videodiagnosis.interfaces.controller;

import com.videodiagnosis.application.service.AnalysisQueryService;
import com.videodiagnosis.application.service.DiagnosisSynthesisQueryService;
import com.videodiagnosis.interfaces.assembler.AnalysisJobAssembler;
import com.videodiagnosis.interfaces.response.AnalysisJobDetailResponse;
import com.videodiagnosis.interfaces.response.AnalysisJobResultResponse;
import com.videodiagnosis.types.common.Result;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/analysis/jobs")
public class AnalysisQueryController {

    private final AnalysisQueryService analysisQueryService;
    private final AnalysisJobAssembler analysisJobAssembler;
    private final DiagnosisSynthesisQueryService diagnosisSynthesisQueryService;

    public AnalysisQueryController(AnalysisQueryService analysisQueryService,
                                   AnalysisJobAssembler analysisJobAssembler,
                                   DiagnosisSynthesisQueryService diagnosisSynthesisQueryService) {
        this.analysisQueryService = analysisQueryService;
        this.analysisJobAssembler = analysisJobAssembler;
        this.diagnosisSynthesisQueryService = diagnosisSynthesisQueryService;
    }

    @GetMapping("/{jobId}")
    public Result<AnalysisJobDetailResponse> getJobDetail(@PathVariable String jobId) {
        return Result.ok(analysisJobAssembler.toDetailResponse(analysisQueryService.getJob(jobId)));
    }

    @GetMapping("/{jobId}/result")
    public Result<AnalysisJobResultResponse> getJobResult(@PathVariable String jobId) {
        return Result.ok(analysisJobAssembler.toResultResponse(analysisQueryService.getResult(jobId)));
    }

    /**
     * Agent 跨维度合成结论：总体总结、改进优先级、待补证据。还没有合成结果时返回空对象。
     */
    @GetMapping("/{jobId}/synthesis")
    public Result<Map<String, Object>> getJobSynthesis(@PathVariable String jobId) {
        return Result.ok(diagnosisSynthesisQueryService.getLatestSynthesis(jobId));
    }

    /**
     * 诊断报告（Markdown）：解析出的评分标准、逐条对照结果、三个维度的结论和补充分析。
     * 浏览器或 curl 直接查看；还没有生成时返回提示。
     */
    @GetMapping(value = "/{jobId}/report", produces = "text/markdown;charset=UTF-8")
    public String getJobReport(@PathVariable String jobId) {
        Object report = diagnosisSynthesisQueryService.getLatestSynthesis(jobId).get("reportMarkdown");
        return report == null ? "# 报告尚未生成\n\n任务还在运行，或该任务由旧版本 agent 生成。\n" : report.toString();
    }
}

