package com.videodiagnosis.application.port;

public interface AgentDispatchPort {

    void dispatch(String jobId, String agentRunId);
}
