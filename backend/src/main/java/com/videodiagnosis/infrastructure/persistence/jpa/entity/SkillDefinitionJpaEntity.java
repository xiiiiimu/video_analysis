package com.videodiagnosis.infrastructure.persistence.jpa.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;
import jakarta.persistence.Index;
import jakarta.persistence.Table;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "skill_definition",
        indexes = {
                @Index(name = "idx_skill_definition_enabled", columnList = "enabled")
        }
)
public class SkillDefinitionJpaEntity {

    @Id
    private String id;
    private String skillKey;
    private String version;
    private String name;
    private String coverageDimension;
    @Column(length = 2000)
    private String toolAllowListJson;
    private boolean enabled;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getSkillKey() { return skillKey; }
    public void setSkillKey(String skillKey) { this.skillKey = skillKey; }
    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getCoverageDimension() { return coverageDimension; }
    public void setCoverageDimension(String coverageDimension) { this.coverageDimension = coverageDimension; }
    public String getToolAllowListJson() { return toolAllowListJson; }
    public void setToolAllowListJson(String toolAllowListJson) { this.toolAllowListJson = toolAllowListJson; }
    public boolean isEnabled() { return enabled; }
    public void setEnabled(boolean enabled) { this.enabled = enabled; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
