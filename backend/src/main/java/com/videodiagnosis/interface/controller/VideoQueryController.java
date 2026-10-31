package com.videodiagnosis.interfaces.controller;

import com.videodiagnosis.application.service.AnalysisQueryService;
import com.videodiagnosis.application.service.VideoAsrQueryService;
import com.videodiagnosis.application.service.VideoFeatureQueryService;
import com.videodiagnosis.interfaces.assembler.VideoAssembler;
import com.videodiagnosis.interfaces.response.VideoDetailResponse;
import com.videodiagnosis.interfaces.response.VideoAsrResponse;
import com.videodiagnosis.interfaces.response.VideoFeatureResponse;
import com.videodiagnosis.types.common.Result;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/videos")
public class VideoQueryController {

    private final AnalysisQueryService analysisQueryService;
    private final VideoAsrQueryService videoAsrQueryService;
    private final VideoFeatureQueryService videoFeatureQueryService;
    private final VideoAssembler videoAssembler;

    public VideoQueryController(AnalysisQueryService analysisQueryService,
                                VideoAsrQueryService videoAsrQueryService,
                                VideoFeatureQueryService videoFeatureQueryService,
                                VideoAssembler videoAssembler) {
        this.analysisQueryService = analysisQueryService;
        this.videoAsrQueryService = videoAsrQueryService;
        this.videoFeatureQueryService = videoFeatureQueryService;
        this.videoAssembler = videoAssembler;
    }

    @GetMapping("/{videoId}")
    public Result<VideoDetailResponse> getVideoDetail(@PathVariable String videoId) {
        return Result.ok(videoAssembler.toDetailResponse(analysisQueryService.getVideo(videoId)));
    }

    @GetMapping("/{videoId}/features")
    public Result<VideoFeatureResponse> getVideoFeatures(@PathVariable String videoId) {
        return Result.ok(videoAssembler.toFeatureResponse(videoFeatureQueryService.getFeature(videoId)));
    }

    @GetMapping("/{videoId}/asr")
    public Result<VideoAsrResponse> getVideoAsr(@PathVariable String videoId) {
        var feature = videoAsrQueryService.getAsrFeature(videoId);
        int wordCount = feature.getTranscriptText() == null || feature.getTranscriptText().isBlank()
                ? 0
                : feature.getTranscriptText().trim().split("\\s+").length;
        return Result.ok(new VideoAsrResponse(
                feature.getVideoAssetId(),
                feature.getId(),
                feature.getTranscriptText(),
                feature.getTranscriptText() == null ? 0 : feature.getTranscriptText().length(),
                wordCount,
                "TRANSCRIBED",
                feature.getCreatedAt()
        ));
    }
}

