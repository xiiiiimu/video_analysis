package com.videodiagnosis.domain.repository;

import com.videodiagnosis.domain.entity.CoverageState;

import java.util.List;

public interface CoverageStateRepository {

    CoverageState save(CoverageState coverageState);

    List<CoverageState> saveAll(List<CoverageState> coverageStates);

    List<CoverageState> findByJobId(String jobId);
}
