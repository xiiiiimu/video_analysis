package com.videodiagnosis.interfaces.exception;

import com.videodiagnosis.types.common.ErrorCode;
import com.videodiagnosis.types.common.Result;
import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(VideoDiagnosisException.class)
    public ResponseEntity<Result<Void>> handleBusiness(VideoDiagnosisException exception) {
        HttpStatus status = exception.getErrorCode().getCode().startsWith("5")
                ? HttpStatus.INTERNAL_SERVER_ERROR
                : HttpStatus.BAD_REQUEST;
        Result<Void> body = Result.fail(exception.getErrorCode());
        if (status == HttpStatus.INTERNAL_SERVER_ERROR) {
            log.error("Business error traceId={} code={}", body.traceId(), exception.getErrorCode().getCode(), exception);
        } else {
            log.warn("Business error traceId={} code={} message={}", body.traceId(), exception.getErrorCode().getCode(), exception.getMessage());
        }
        return ResponseEntity.status(status).body(body);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Result<Void>> handleValidation(MethodArgumentNotValidException exception) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(Result.fail(ErrorCode.BAD_REQUEST.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Result<Void>> handleException(Exception exception) {
        // 改造前这里不打日志，响应里的 traceId 在日志里根本搜不到，ffmpeg 之类的失败完全无从排查
        Result<Void> body = Result.fail(ErrorCode.INTERNAL_ERROR.getMessage());
        log.error("Unhandled error traceId={}", body.traceId(), exception);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(body);
    }
}

