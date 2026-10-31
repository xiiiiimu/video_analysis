package com.videodiagnosis.types.enums;

public enum PriorityEnum {
    P0(0),
    P1(1),
    P2(2);

    private final int weight;

    PriorityEnum(int weight) {
        this.weight = weight;
    }

    public int getWeight() {
        return weight;
    }
}
