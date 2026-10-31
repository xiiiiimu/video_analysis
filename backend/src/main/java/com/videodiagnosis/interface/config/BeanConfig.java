package com.videodiagnosis.interfaces.config;

import com.videodiagnosis.interfaces.assembler.AnalysisJobAssembler;
import com.videodiagnosis.interfaces.assembler.VideoAssembler;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class BeanConfig {

    @Bean
    public AnalysisJobAssembler analysisJobAssembler() {
        return new AnalysisJobAssembler();
    }

    @Bean
    public VideoAssembler videoAssembler() {
        return new VideoAssembler();
    }
}

