package com.videodiagnosis.infrastructure.persistence.mapper;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.domain.valueobject.VideoMeta;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class PersistenceMapper {

    private final ObjectMapper objectMapper;

    public PersistenceMapper(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public String writeList(List<String> values) {
        try {
            return values == null ? "[]" : objectMapper.writeValueAsString(values);
        } catch (JsonProcessingException ex) {
            throw new IllegalStateException("Failed to serialize list", ex);
        }
    }

    public List<String> readList(String json) {
        try {
            if (json == null || json.isBlank()) {
                return List.of();
            }
            return objectMapper.readValue(json, new TypeReference<List<String>>() {});
        } catch (JsonProcessingException ex) {
            throw new IllegalStateException("Failed to deserialize list", ex);
        }
    }

    public String writeObject(Object value) {
        try {
            return value == null ? "{}" : objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException ex) {
            throw new IllegalStateException("Failed to serialize object", ex);
        }
    }

    public <T> T readObject(String json, Class<T> type) {
        try {
            if (json == null || json.isBlank()) {
                return null;
            }
            return objectMapper.readValue(json, type);
        } catch (JsonProcessingException ex) {
            throw new IllegalStateException("Failed to deserialize object", ex);
        }
    }

    public String writeVideoMeta(VideoMeta meta) {
        return writeObject(meta);
    }

    public VideoMeta readVideoMeta(String json) {
        return readObject(json, VideoMeta.class);
    }
}