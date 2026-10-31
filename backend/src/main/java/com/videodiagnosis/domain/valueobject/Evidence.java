package com.videodiagnosis.domain.valueobject;

import java.util.ArrayList;
import java.util.List;

public record Evidence(List<String> target, List<String> reference, List<String> notes) {

    public Evidence {
        target = target == null ? List.of() : List.copyOf(target);
        reference = reference == null ? List.of() : List.copyOf(reference);
        notes = notes == null ? List.of() : List.copyOf(notes);
    }

    public static Evidence empty() {
        return new Evidence(List.of(), List.of(), List.of());
    }

    public static Evidence of(String targetItem, String referenceItem, String note) {
        List<String> target = new ArrayList<>();
        List<String> reference = new ArrayList<>();
        List<String> notes = new ArrayList<>();
        if (targetItem != null && !targetItem.isBlank()) {
            target.add(targetItem);
        }
        if (referenceItem != null && !referenceItem.isBlank()) {
            reference.add(referenceItem);
        }
        if (note != null && !note.isBlank()) {
            notes.add(note);
        }
        return new Evidence(target, reference, notes);
    }
}
