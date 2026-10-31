package com.videodiagnosis.infrastructure.persistence.repository;

import com.videodiagnosis.domain.entity.SkillDefinition;
import com.videodiagnosis.domain.repository.SkillDefinitionRepository;
import com.videodiagnosis.infrastructure.persistence.jpa.repository.SkillDefinitionJpaRepository;
import com.videodiagnosis.infrastructure.persistence.mapper.PersistenceConverter;
import com.videodiagnosis.types.enums.AnalysisDimensionEnum;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@Primary
public class JpaSkillDefinitionRepository implements SkillDefinitionRepository {

    private final SkillDefinitionJpaRepository repository;
    private final PersistenceConverter converter;

    public JpaSkillDefinitionRepository(SkillDefinitionJpaRepository repository, PersistenceConverter converter) {
        this.repository = repository;
        this.converter = converter;
    }

    @Override
    public SkillDefinition save(SkillDefinition definition) {
        repository.save(converter.toEntity(definition));
        return definition;
    }

    @Override
    public Optional<SkillDefinition> findBySkillKey(String skillKey) {
        return repository.findBySkillKey(skillKey).map(converter::toDomain);
    }

    @Override
    public Optional<SkillDefinition> findByDimension(AnalysisDimensionEnum dimension) {
        return repository.findByEnabledTrue().stream()
                .map(converter::toDomain)
                .filter(definition -> definition.getCoverageDimension() == dimension)
                .findFirst();
    }

    @Override
    public List<SkillDefinition> findEnabled() {
        return repository.findByEnabledTrue().stream().map(converter::toDomain).toList();
    }
}