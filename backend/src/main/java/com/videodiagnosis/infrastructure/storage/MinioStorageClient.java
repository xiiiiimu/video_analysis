package com.videodiagnosis.infrastructure.storage;

import io.minio.BucketExistsArgs;
import io.minio.GetObjectArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import java.io.OutputStream;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.UUID;

@Component
public class MinioStorageClient {

    private final MinioClient minioClient;
    private final ObjectStorageProperties properties;

    public MinioStorageClient(MinioClient minioClient, ObjectStorageProperties properties) {
        this.minioClient = minioClient;
        this.properties = properties;
    }

    @PostConstruct
    public void initBucket() throws Exception {
        if (!properties.isInitializeBucket()) {
            return;
        }
        boolean exists = minioClient.bucketExists(
                BucketExistsArgs.builder().bucket(properties.getBucket()).build()
        );
        if (!exists) {
            minioClient.makeBucket(
                    MakeBucketArgs.builder().bucket(properties.getBucket()).build()
            );
        }
    }

    public StoredObject uploadVideo(MultipartFile file, String role) {
        try {
            String extension = resolveExtension(file.getOriginalFilename(), file.getContentType());
            String objectName = String.format(
                    Locale.ROOT,
                    "%s/%s/%s%s",
                    "videos",
                    role == null || role.isBlank() ? "unknown" : role.toLowerCase(Locale.ROOT),
                    UUID.randomUUID().toString().replace("-", ""),
                    extension
            );
            try (InputStream inputStream = file.getInputStream()) {
                minioClient.putObject(
                        PutObjectArgs.builder()
                                .bucket(properties.getBucket())
                                .object(objectName)
                                .stream(inputStream, file.getSize(), -1)
                                .contentType(file.getContentType() == null ? "application/octet-stream" : file.getContentType())
                                .build()
                );
            }
            String publicUrl = properties.getPublicBaseUrl() + "/" + properties.getBucket() + "/" + objectName;
            return new StoredObject(objectName, publicUrl);
        } catch (Exception ex) {
            throw new IllegalStateException("Failed to upload file to object storage", ex);
        }
    }

    public Path downloadTo(String fileUrl, Path target) {
        String objectName = resolveObjectName(fileUrl);
        try (InputStream inputStream = minioClient.getObject(
                GetObjectArgs.builder()
                        .bucket(properties.getBucket())
                        .object(objectName)
                        .build()
        );
             OutputStream outputStream = Files.newOutputStream(target)) {
            inputStream.transferTo(outputStream);
            return target;
        } catch (Exception ex) {
            throw new IllegalStateException("Failed to download file from object storage", ex);
        }
    }

    public StoredObject uploadFrame(Path framePath, String videoAssetId, int index) {
        String objectName = String.format(
                Locale.ROOT,
                "frames/%s/frame-%03d.jpg",
                videoAssetId == null || videoAssetId.isBlank() ? "unknown" : videoAssetId,
                index
        );
        try (InputStream inputStream = Files.newInputStream(framePath)) {
            minioClient.putObject(
                    PutObjectArgs.builder()
                            .bucket(properties.getBucket())
                            .object(objectName)
                            .stream(inputStream, Files.size(framePath), -1)
                            .contentType("image/jpeg")
                            .build()
            );
            String publicUrl = properties.getPublicBaseUrl() + "/" + properties.getBucket() + "/" + objectName;
            return new StoredObject(objectName, publicUrl);
        } catch (Exception ex) {
            throw new IllegalStateException("Failed to upload frame to object storage", ex);
        }
    }

    private String resolveObjectName(String fileUrl) {
        if (fileUrl == null || fileUrl.isBlank()) {
            throw new IllegalArgumentException("File url is blank");
        }
        String s3Prefix = "s3://" + properties.getBucket() + "/";
        if (fileUrl.startsWith(s3Prefix)) {
            return fileUrl.substring(s3Prefix.length());
        }
        String bucketPath = "/" + properties.getBucket() + "/";
        int bucketIndex = fileUrl.indexOf(bucketPath);
        if (bucketIndex >= 0) {
            return fileUrl.substring(bucketIndex + bucketPath.length());
        }
        throw new IllegalArgumentException("Unsupported object storage url: " + fileUrl);
    }

    private String resolveExtension(String filename, String contentType) {
        if (filename != null && filename.contains(".")) {
            return filename.substring(filename.lastIndexOf('.'));
        }
        if (contentType != null) {
            if (contentType.contains("mp4")) {
                return ".mp4";
            }
            if (contentType.contains("mov") || contentType.contains("quicktime")) {
                return ".mov";
            }
        }
        return ".bin";
    }

    public record StoredObject(String objectName, String publicUrl) {
    }
}
