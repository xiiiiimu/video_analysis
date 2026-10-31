package com.videodiagnosis.application.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.videodiagnosis.infrastructure.persistence.repository.DiagnosisResultRecordRepository;
import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * 查询 agent-service 生成的跨维度合成结论（总体总结、改进优先级、待补证据）。
 */
@Service
public class DiagnosisSynthesisQueryService {

    private final AnalysisQueryService analysisQueryService;
    private final DiagnosisResultRecordRepository resultRecordRepository;
    private final ObjectMapper objectMapper;

    public DiagnosisSynthesisQueryService(AnalysisQueryService analysisQueryService,
                                          DiagnosisResultRecordRepository resultRecordRepository,
                                          ObjectMapper objectMapper) {
        this.analysisQueryService = analysisQueryService;
        this.resultRecordRepository = resultRecordRepository;
        this.objectMapper = objectMapper;
    }

    public Map<String, Object> getLatestSynthesis(String jobId) {
        analysisQueryService.getJob(jobId);
        String json = resultRecordRepository.findLatestSynthesisJson(jobId).orElse(null);
        if (json == null || json.isBlank()) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {});
        } catch (JsonProcessingException ex) {
            throw new VideoDiagnosisException(ErrorCode.INTERNAL_ERROR, "Invalid synthesis snapshot");
        }
    }
}
