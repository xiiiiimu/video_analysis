package com.videodiagnosis.domain.entity;

import com.videodiagnosis.types.enums.AnalysisDimensionEnum;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

public class SkillDefinition {

    private String id;
    private String skillKey;
    private String version;
    private String name;
    private AnalysisDimensionEnum coverageDimension;
    private List<String> toolAllowList = new ArrayList<>();
    private boolean enabled;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public SkillDefinition() {
    }

    public SkillDefinition(String skillKey, String version, String name, AnalysisDimensionEnum coverageDimension, List<String> toolAllowList, boolean enabled) {
        this.skillKey = skillKey;
        this.version = version;
        this.name = name;
        this.coverageDimension = coverageDimension;
        this.toolAllowList = toolAllowList == null ? new ArrayList<>() : new ArrayList<>(toolAllowList);
        this.enabled = enabled;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getSkillKey() {
        return skillKey;
    }

    public void setSkillKey(String skillKey) {
        this.skillKey = skillKey;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public AnalysisDimensionEnum getCoverageDimension() {
        return coverageDimension;
    }

    public void setCoverageDimension(AnalysisDimensionEnum coverageDimension) {
        this.coverageDimension = coverageDimension;
    }

    public List<String> getToolAllowList() {
        return toolAllowList;
    }

    public void setToolAllowList(List<String> toolAllowList) {
        this.toolAllowList = toolAllowList == null ? new ArrayList<>() : new ArrayList<>(toolAllowList);
    }

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
