package com.videodiagnosis.interfaces.controller;

import com.videodiagnosis.application.command.CreateVideoCommand;
import com.videodiagnosis.application.service.VideoCommandService;
import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.interfaces.assembler.VideoAssembler;
import com.videodiagnosis.interfaces.request.CreateVideoRequest;
import com.videodiagnosis.interfaces.response.UploadVideoResponse;
import com.videodiagnosis.interfaces.response.VideoDetailResponse;
import com.videodiagnosis.types.common.Result;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/videos")
public class VideoCommandController {

    private final VideoCommandService videoCommandService;
    private final VideoAssembler videoAssembler;

    public VideoCommandController(VideoCommandService videoCommandService, VideoAssembler videoAssembler) {
        this.videoCommandService = videoCommandService;
        this.videoAssembler = videoAssembler;
    }

    @PostMapping
    public Result<VideoDetailResponse> registerVideo(@Valid @RequestBody CreateVideoRequest request) {
        CreateVideoCommand command = new CreateVideoCommand(
                request.role(),
                request.fileUrl(),
                request.title(),
                request.description(),
                request.coverUrl()
        );
        VideoAsset asset = videoCommandService.registerVideo(command);
        return Result.ok(videoAssembler.toDetailResponse(asset));
    }

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Result<UploadVideoResponse> uploadVideo(@RequestPart("file") MultipartFile file,
                                                   @RequestPart("role") String role,
                                                   @RequestPart(value = "title", required = false) String title,
                                                   @RequestPart(value = "description", required = false) String description,
                                                   @RequestPart(value = "coverUrl", required = false) String coverUrl) {
        CreateVideoCommand command = new CreateVideoCommand(role, null, title, description, coverUrl);
        VideoCommandService.StoredVideo storedVideo = videoCommandService.uploadAndRegisterVideo(command, file);
        return Result.ok(new UploadVideoResponse(
                storedVideo.asset().getId(),
                storedVideo.objectName(),
                storedVideo.fileUrl(),
                storedVideo.asset().getTitle(),
                String.valueOf(storedVideo.asset().getStatus())
        ));
    }
}