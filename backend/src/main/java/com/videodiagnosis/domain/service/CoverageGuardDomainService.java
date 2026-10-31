package com.videodiagnosis.domain.service;

import com.videodiagnosis.domain.entity.CoverageState;
import com.videodiagnosis.types.enums.AnalysisDimensionEnum;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

@Service
public class CoverageGuardDomainService {

    private static final Set<AnalysisDimensionEnum> CORE_DIMENSIONS = EnumSet.of(
            AnalysisDimensionEnum.HOOK,
            AnalysisDimensionEnum.STRUCTURE_RHYTHM,
            AnalysisDimensionEnum.VALUE_DELIVERY
    );

    public List<CoverageState> buildCoverageStates(String jobId) {
        List<CoverageState> states = new ArrayList<>();
        for (AnalysisDimensionEnum dimension : AnalysisDimensionEnum.values()) {
            CoverageState coverageState = new CoverageState();
            coverageState.setId(UUID.randomUUID().toString());
            coverageState.setJobId(jobId);
            coverageState.setDimension(dimension);
            coverageState.setState(CORE_DIMENSIONS.contains(dimension) ? "checked" : "unchecked");
            coverageState.setReason(CORE_DIMENSIONS.contains(dimension) ? "MVP core dimension covered" : "Not in MVP core flow");
            coverageState.setCreatedAt(LocalDateTime.now());
            coverageState.setUpdatedAt(LocalDateTime.now());
            states.add(coverageState);
        }
        return states;
    }
}
