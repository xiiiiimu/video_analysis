package com.videodiagnosis.types.common;

public class VideoDiagnosisException extends RuntimeException {

    private final ErrorCode errorCode;

    public VideoDiagnosisException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }

    public VideoDiagnosisException(ErrorCode errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public ErrorCode getErrorCode() {
        return errorCode;
    }
}
