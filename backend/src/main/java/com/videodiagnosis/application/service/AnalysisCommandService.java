package com.videodiagnosis.application.service;

import com.videodiagnosis.application.usecase.CreateAnalysisJobCase;
import com.videodiagnosis.application.command.CreateAnalysisJobCommand;
import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.application.view.AnalysisJobCreationResult;
import org.springframework.stereotype.Service;

@Service
public class AnalysisCommandService {

    private final CreateAnalysisJobCase createAnalysisJobCase;

    public AnalysisCommandService(CreateAnalysisJobCase createAnalysisJobCase) {
        this.createAnalysisJobCase = createAnalysisJobCase;
    }

    public AnalysisJob createAnalysisJob(CreateAnalysisJobCommand command) {
        AnalysisJobCreationResult result = createAnalysisJobCase.execute(command);
        return result.job();
    }
}
