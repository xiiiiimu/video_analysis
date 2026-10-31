package com.videodiagnosis.infrastructure.client;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * 语音转写（OpenAI 兼容 /audio/transcriptions 接口）配置。
 *
 * <p>apiKey 为空时自动关闭 ASR，不影响其它预处理。
 */
@ConfigurationProperties(prefix = "app.asr")
public class AsrProperties {

    private boolean enabled = true;
    private String apiKey = "";
    private String baseUrl = "https://api.openai.com/v1";
    /** whisper-1 支持 verbose_json 分段时间戳；OpenAI 公告 whisper-1 将于 2027-02-26 下线，届时改为 gpt-transcribe（自动走 chunked）。 */
    private String model = "whisper-1";
    /** 可选的语言提示，如 zh；留空由模型自动识别。 */
    private String language = "";
    /**
     * auto：whisper 系列用 segments，其它模型用 chunked；
     * segments：一次请求，用 verbose_json 返回的分段时间戳；
     * chunked：按 chunkSeconds 切片分别转写，时间戳精度 = 切片长度，适用于不返回时间戳的模型。
     */
    private String mode = "auto";
    private int chunkSeconds = 15;
    private int connectTimeoutMs = 10000;
    private int readTimeoutMs = 120000;

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public String getApiKey() {
        return apiKey;
    }

    public void setApiKey(String apiKey) {
        this.apiKey = apiKey;
    }

    public String getBaseUrl() {
        return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public String getModel() {
        return model;
    }

    public void setModel(String model) {
        this.model = model;
    }

    public String getLanguage() {
        return language;
    }

    public void setLanguage(String language) {
        this.language = language;
    }

    public String getMode() {
        return mode;
    }

    public void setMode(String mode) {
        this.mode = mode;
    }

    public int getChunkSeconds() {
        return chunkSeconds;
    }

    public void setChunkSeconds(int chunkSeconds) {
        this.chunkSeconds = chunkSeconds;
    }

    public int getConnectTimeoutMs() {
        return connectTimeoutMs;
    }

    public void setConnectTimeoutMs(int connectTimeoutMs) {
        this.connectTimeoutMs = connectTimeoutMs;
    }

    public int getReadTimeoutMs() {
        return readTimeoutMs;
    }

    public void setReadTimeoutMs(int readTimeoutMs) {
        this.readTimeoutMs = readTimeoutMs;
    }

    public boolean isActive() {
        return enabled && apiKey != null && !apiKey.isBlank();
    }

    public boolean useSegmentMode() {
        String resolved = mode == null ? "auto" : mode.trim().toLowerCase();
        if ("segments".equals(resolved)) {
            return true;
        }
        if ("chunked".equals(resolved)) {
            return false;
        }
        return model != null && model.toLowerCase().startsWith("whisper");
    }
}
