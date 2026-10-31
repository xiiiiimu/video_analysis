package com.videodiagnosis.infrastructure.persistence.jpa.repository;

import com.videodiagnosis.infrastructure.persistence.jpa.entity.SkillDefinitionJpaEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface SkillDefinitionJpaRepository extends JpaRepository<SkillDefinitionJpaEntity, String> {
    Optional<SkillDefinitionJpaEntity> findBySkillKey(String skillKey);
    List<SkillDefinitionJpaEntity> findByEnabledTrue();
}