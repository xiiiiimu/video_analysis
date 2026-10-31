package com.videodiagnosis.application.workflow;

import com.videodiagnosis.domain.entity.AnalysisJob;
import com.videodiagnosis.domain.entity.CoverageState;
import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.domain.entity.VideoFeature;
import com.videodiagnosis.domain.repository.CoverageStateRepository;
import com.videodiagnosis.domain.service.CoverageGuardDomainService;
import com.videodiagnosis.domain.service.DiagnosisDomainService;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class DiagnosisWorkflow {

    private final DiagnosisDomainService diagnosisDomainService;
    private final CoverageGuardDomainService coverageGuardDomainService;
    private final CoverageStateRepository coverageStateRepository;

    public DiagnosisWorkflow(DiagnosisDomainService diagnosisDomainService,
                             CoverageGuardDomainService coverageGuardDomainService,
                             CoverageStateRepository coverageStateRepository) {
        this.diagnosisDomainService = diagnosisDomainService;
        this.coverageGuardDomainService = coverageGuardDomainService;
        this.coverageStateRepository = coverageStateRepository;
    }

    public List<Finding> execute(AnalysisJob job, VideoFeature targetFeature, List<VideoFeature> referenceFeatures) {
        List<Finding> findings = diagnosisDomainService.diagnose(job.getId(), targetFeature, referenceFeatures);
        List<CoverageState> coverageStates = coverageGuardDomainService.buildCoverageStates(job.getId());
        coverageStateRepository.saveAll(coverageStates);
        return findings;
    }
}
