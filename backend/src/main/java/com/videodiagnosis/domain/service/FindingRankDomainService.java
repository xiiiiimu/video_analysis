package com.videodiagnosis.domain.service;

import com.videodiagnosis.domain.entity.Finding;
import com.videodiagnosis.types.enums.PriorityEnum;
import org.springframework.stereotype.Service;

import java.util.Comparator;
import java.util.List;

@Service
public class FindingRankDomainService {

    public List<Finding> rankAndLimit(List<Finding> findings, int limit) {
        return findings.stream()
                .sorted(Comparator
                        .comparing((Finding finding) -> finding.getPriority() == null ? PriorityEnum.P2.getWeight() : finding.getPriority().getWeight())
                        .thenComparing(Finding::getConfidence, Comparator.reverseOrder()))
                .limit(limit)
                .toList();
    }
}
