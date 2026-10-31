package com.videodiagnosis.domain.repository;

import com.videodiagnosis.domain.entity.Finding;

import java.util.List;

public interface FindingRepository {

    Finding save(Finding finding);

    List<Finding> saveAll(List<Finding> findings);

    List<Finding> findByJobId(String jobId);
}
