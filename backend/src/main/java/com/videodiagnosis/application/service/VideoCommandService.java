package com.videodiagnosis.application.service;

import com.videodiagnosis.application.command.CreateVideoCommand;
import com.videodiagnosis.domain.entity.VideoAsset;
import com.videodiagnosis.domain.repository.VideoAssetRepository;
import com.videodiagnosis.infrastructure.media.FfmpegMediaAdapter;
import com.videodiagnosis.infrastructure.storage.MinioStorageClient;
import com.videodiagnosis.types.common.CommonConstants;
import com.videodiagnosis.types.enums.VideoStatusEnum;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class VideoCommandService {

    private final VideoAssetRepository videoAssetRepository;
    private final FfmpegMediaAdapter ffmpegMediaAdapter;
    private final MinioStorageClient minioStorageClient;
    private final VideoFeatureCommandService videoFeatureCommandService;

    public VideoCommandService(VideoAssetRepository videoAssetRepository,
                               FfmpegMediaAdapter ffmpegMediaAdapter,
                               MinioStorageClient minioStorageClient,
                               VideoFeatureCommandService videoFeatureCommandService) {
        this.videoAssetRepository = videoAssetRepository;
        this.ffmpegMediaAdapter = ffmpegMediaAdapter;
        this.minioStorageClient = minioStorageClient;
        this.videoFeatureCommandService = videoFeatureCommandService;
    }

    public VideoAsset registerVideo(CreateVideoCommand command) {
        VideoAsset asset = new VideoAsset();
        asset.setId(UUID.randomUUID().toString());
        asset.setOwnerId(CommonConstants.DEFAULT_USER_ID);
        asset.setRole(command.role());
        asset.setTitle(command.title());
        asset.setDescription(command.description());
        asset.setCoverUrl(command.coverUrl());
        asset.setFileUrl(command.fileUrl());
        asset.setFileSize(0L);
        asset.setStatus(VideoStatusEnum.UPLOADING);
        asset.setCreatedAt(LocalDateTime.now());
        asset.setUpdatedAt(LocalDateTime.now());
        asset.markReady(ffmpegMediaAdapter.extractMeta(command.fileUrl()));
        videoAssetRepository.save(asset);
        return asset;
    }

    public StoredVideo uploadAndRegisterVideo(CreateVideoCommand command, MultipartFile file) {
        MinioStorageClient.StoredObject storedObject = minioStorageClient.uploadVideo(file, command.role());
        CreateVideoCommand storageCommand = new CreateVideoCommand(
                command.role(),
                storedObject.publicUrl(),
                command.title(),
                command.description(),
                command.coverUrl()
        );
        VideoAsset asset = registerVideo(storageCommand);
        videoFeatureCommandService.extractAndStoreKeyframes(asset.getId());
        VideoAsset latestAsset = videoAssetRepository.findById(asset.getId()).orElse(asset);
        return new StoredVideo(latestAsset, storedObject.objectName(), storedObject.publicUrl());
    }

    public record StoredVideo(VideoAsset asset, String objectName, String fileUrl) {
    }
}
