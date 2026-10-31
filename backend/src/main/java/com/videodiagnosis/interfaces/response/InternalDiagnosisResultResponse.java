package com.videodiagnosis.interfaces.response;

import java.util.List;

/**
 * @param duplicate true 表示该 idempotencyKey 之前已经保存过，本次没有写入新数据
 */
public record InternalDiagnosisResultResponse(
        String jobId,
        List<String> findingIds,
        boolean duplicate
) {
}
