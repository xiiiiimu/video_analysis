package com.videodiagnosis.interfaces.controller;

import com.videodiagnosis.types.common.Result;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/health")
public class HealthQueryController {

    @GetMapping
    public Result<Map<String, String>> health() {
        return Result.ok(Map.of("status", "UP"));
    }
}

