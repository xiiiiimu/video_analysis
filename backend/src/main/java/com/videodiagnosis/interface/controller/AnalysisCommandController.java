package com.videodiagnosis.interfaces.controller;

import com.videodiagnosis.application.command.CreateAnalysisJobCommand;
import com.videodiagnosis.application.service.AnalysisCommandService;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.interfaces.assembler.AnalysisJobAssembler;
import com.videodiagnosis.interfaces.request.CreateAnalysisJobRequest;
import com.videodiagnosis.interfaces.response.CreateAnalysisJobResponse;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.Result;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;

@RestController
@RequestMapping("/api/v1/analysis")
public class AnalysisCommandController {

    private final AnalysisCommandService analysisCommandService;
    private final AnalysisJobAssembler analysisJobAssembler;

    public AnalysisCommandController(AnalysisCommandService analysisCommandService,
                                     AnalysisJobAssembler analysisJobAssembler) {
        this.analysisCommandService = analysisCommandService;
        this.analysisJobAssembler = analysisJobAssembler;
    }

    @PostMapping("/jobs")
    public Result<CreateAnalysisJobResponse> createAnalysisJob(@Valid @RequestBody CreateAnalysisJobRequest request) {
        CreateAnalysisJobCommand command = new CreateAnalysisJobCommand(
                request.targetVideoId(),
                request.referenceVideoIds(),
                request.targetTitle(),
                request.targetDescription(),
                request.referenceTitles(),
                request.referenceDescriptions(),
                request.enableCoverAnalysis(),
                request.enablePerformanceAnalysis(),
                request.criteriaText(),
                request.supplementaryAnalysis(),
                request.category()
        );
        AnalysisJob job = analysisCommandService.createAnalysisJob(command);
        return Result.ok(analysisJobAssembler.toCreateResponse(job));
    }

    /**
     * 上传评分标准 txt + 指定目标 / 参考视频创建任务：
     * {@code curl -F targetVideoId=... -F referenceVideoIds=... -F criteria=@标准.txt -F supplementaryAnalysis=false}
     */
    @PostMapping(value = "/jobs/with-criteria", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Result<CreateAnalysisJobResponse> createAnalysisJobWithCriteria(
            @RequestParam("targetVideoId") String targetVideoId,
            @RequestParam("referenceVideoIds") List<String> referenceVideoIds,
            @RequestPart("criteria") MultipartFile criteria,
            @RequestParam(value = "targetTitle", required = false) String targetTitle,
            @RequestParam(value = "supplementaryAnalysis", defaultValue = "false") boolean supplementaryAnalysis,
            @RequestParam(value = "category", required = false) String category) {
        List<String> references = referenceVideoIds.stream()
                .flatMap(item -> Arrays.stream(item.split(",")))
                .map(String::trim)
                .filter(item -> !item.isEmpty())
                .toList();
        if (targetVideoId == null || targetVideoId.isBlank() || references.isEmpty()) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, "targetVideoId and referenceVideoIds are required");
        }
        CreateAnalysisJobCommand command = new CreateAnalysisJobCommand(
                targetVideoId.trim(),
                references,
                targetTitle,
                null,
                List.of(),
                List.of(),
                false,
                false,
                readCriteria(criteria),
                supplementaryAnalysis,
                category
        );
        AnalysisJob job = analysisCommandService.createAnalysisJob(command);
        return Result.ok(analysisJobAssembler.toCreateResponse(job));
    }

    static String readCriteria(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, "criteria file is empty");
        }
        String text;
        try {
            text = new String(file.getBytes(), StandardCharsets.UTF_8);
        } catch (IOException ex) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, "Unable to read criteria file");
        }
        if (text.startsWith("\uFEFF")) {
            text = text.substring(1);  // Windows 记事本保存的 UTF-8 BOM
        }
        if (text.indexOf('\u0000') >= 0 || text.indexOf('\uFFFD') >= 0) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, "criteria must be a UTF-8 text file");
        }
        if (text.isBlank()) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST, "criteria file is empty");
        }
        if (text.length() > CreateAnalysisJobRequest.MAX_CRITERIA_CHARS) {
            throw new VideoDiagnosisException(ErrorCode.BAD_REQUEST,
                    "criteria is too long (max " + CreateAnalysisJobRequest.MAX_CRITERIA_CHARS + " chars)");
        }
        return text;
    }
}

