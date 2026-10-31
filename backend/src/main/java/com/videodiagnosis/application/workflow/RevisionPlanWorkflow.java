package com.videodiagnosis.application.workflow;

import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.service.FindingRankDomainService;
import com.videodiagnosis.infrastructure.client.ModelClientAdapter;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class RevisionPlanWorkflow {

    private final FindingRankDomainService findingRankDomainService;
    private final ModelClientAdapter modelClientAdapter;

    public RevisionPlanWorkflow(FindingRankDomainService findingRankDomainService,
                                ModelClientAdapter modelClientAdapter) {
        this.findingRankDomainService = findingRankDomainService;
        this.modelClientAdapter = modelClientAdapter;
    }

    public List<String> execute(List<Finding> findings) {
        List<Finding> ranked = findingRankDomainService.rankAndLimit(findings, 3);
        return List.of(modelClientAdapter.summarizeFindings(ranked));
    }
}
