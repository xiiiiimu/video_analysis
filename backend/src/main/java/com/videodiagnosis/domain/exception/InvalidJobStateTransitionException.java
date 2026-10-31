package com.videodiagnosis.domain.exception;

import com.videodiagnosis.types.enums.JobStatusEnum;

public class InvalidJobStateTransitionException extends RuntimeException {

    public InvalidJobStateTransitionException(JobStatusEnum current, JobStatusEnum target) {
        super("Invalid AnalysisJob state transition: " + current + " -> " + target);
    }
}
