package com.videodiagnosis.domain.repository;

import com.videodiagnosis.domain.entity.SkillDefinition;
import com.videodiagnosis.types.enums.AnalysisDimensionEnum;

import java.util.List;
import java.util.Optional;

public interface SkillDefinitionRepository {

    SkillDefinition save(SkillDefinition definition);

    Optional<SkillDefinition> findBySkillKey(String skillKey);

    Optional<SkillDefinition> findByDimension(AnalysisDimensionEnum dimension);

    List<SkillDefinition> findEnabled();
}
