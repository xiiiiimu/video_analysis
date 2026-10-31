package com.videodiagnosis.infrastructure.repository;

import com.videodiagnosis.domain.entity.SkillDefinition;
import com.videodiagnosis.domain.repository.SkillDefinitionRepository;
import com.videodiagnosis.types.enums.AnalysisDimensionEnum;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class InMemorySkillDefinitionRepository implements SkillDefinitionRepository {

    private final Map<String, SkillDefinition> byKey = new ConcurrentHashMap<>();

    @PostConstruct
    public void init() {
        save(new SkillDefinition("hook_analysis", "0.1.0", "Hook Analysis", AnalysisDimensionEnum.HOOK, List.of("asr", "frames"), true));
        save(new SkillDefinition("structure_rhythm_analysis", "0.1.0", "Structure Rhythm Analysis", AnalysisDimensionEnum.STRUCTURE_RHYTHM, List.of("asr", "frames"), true));
        save(new SkillDefinition("value_delivery_analysis", "0.1.0", "Value Delivery Analysis", AnalysisDimensionEnum.VALUE_DELIVERY, List.of("asr", "frames"), true));
    }

    @Override
    public SkillDefinition save(SkillDefinition definition) {
        if (definition.getId() == null) {
            definition.setId(UUID.randomUUID().toString());
        }
        byKey.put(definition.getSkillKey(), definition);
        return definition;
    }

    @Override
    public Optional<SkillDefinition> findBySkillKey(String skillKey) {
        return Optional.ofNullable(byKey.get(skillKey));
    }

    @Override
    public Optional<SkillDefinition> findByDimension(AnalysisDimensionEnum dimension) {
        return byKey.values().stream().filter(item -> item.isEnabled() && item.getCoverageDimension() == dimension).findFirst();
    }

    @Override
    public List<SkillDefinition> findEnabled() {
        return byKey.values().stream().filter(SkillDefinition::isEnabled).toList();
    }
}
