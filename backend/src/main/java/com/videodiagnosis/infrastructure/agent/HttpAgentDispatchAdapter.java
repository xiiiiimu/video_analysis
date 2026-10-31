package com.videodiagnosis.infrastructure.agent;

import com.videodiagnosis.application.port.AgentDispatchPort;
import com.videodiagnosis.infrastructure.client.AgentServiceHttpClient;
import org.springframework.stereotype.Component;

@Component
public class HttpAgentDispatchAdapter implements AgentDispatchPort {

    private final AgentServiceHttpClient agentServiceHttpClient;

    public HttpAgentDispatchAdapter(AgentServiceHttpClient agentServiceHttpClient) {
        this.agentServiceHttpClient = agentServiceHttpClient;
    }

    @Override
    public void dispatch(String jobId, String agentRunId) {
        agentServiceHttpClient.submitJob(jobId, agentRunId);
    }
}
