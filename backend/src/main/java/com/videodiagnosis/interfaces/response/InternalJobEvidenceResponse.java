package com.videodiagnosis.interfaces.response;

import java.util.List;

public record InternalJobEvidenceResponse(
        String jobId,
        String targetVideoId,
        InternalVideoEvidenceResponse targetEvidence,
        List<InternalVideoEvidenceResponse> referenceEvidence
) {
}
