package com.videodiagnosis.types.common;

public enum ErrorCode {
    BAD_REQUEST("40001", "Bad request"),
    VIDEO_NOT_FOUND("40002", "Video not found"),
    REFERENCE_VIDEO_MISSING("40003", "Reference video missing"),
    JOB_NOT_FOUND("40004", "Analysis job not found"),
    PREPROCESS_FAILED("50001", "Preprocess failed"),
    ASR_FAILED("50002", "ASR failed"),
    MODEL_FAILED("50003", "Model call failed"),
    RESULT_BUILD_FAILED("50004", "Result build failed"),
    INTERNAL_ERROR("50000", "Internal error");

    private final String code;
    private final String message;

    ErrorCode(String code, String message) {
        this.code = code;
        this.message = message;
    }

    public String getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }
}
