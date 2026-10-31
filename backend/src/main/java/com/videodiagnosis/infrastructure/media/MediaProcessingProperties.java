package com.videodiagnosis.infrastructure.media;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.media")
public class MediaProcessingProperties {

    private String ffmpegPath = "ffmpeg";
    private String ffprobePath = "ffprobe";
    private String tesseractPath = "tesseract";
    private String tesseractLanguages = "chi_sim+eng";
    private int keyframeCount = 5;
    private int keyframeIntervalSeconds = 3;
    private int ocrFrameCount = 5;
    private int ocrFrameIntervalSeconds = 3;
    private boolean ocrEnabled = true;

    // ---- 2 分钟分段抽帧（v0.2）----
    // 旧的 keyframeCount / keyframeIntervalSeconds / ocrFrame* 只覆盖前 15 秒，已不再用于抽帧，保留字段仅为兼容旧配置。
    /** 分析窗口：只分析视频前 N 秒，超出部分在 timeline 里标记 truncated。 */
    private int analysisWindowSeconds = 120;
    /** 开场钩子密集采样区间（秒）。 */
    private int hookDenseSeconds = 5;
    /** 开场钩子区间内的采样间隔（秒）。 */
    private double hookFrameIntervalSeconds = 1.0;
    /** 钩子区间之后的均匀采样间隔（秒）。 */
    private double frameIntervalSeconds = 3.0;
    /** ffmpeg 场景切换阈值，0~1，越小越敏感。 */
    private double sceneThreshold = 0.3;
    /** 与已有采样点距离小于该值的场景切换帧不再重复抽取（秒）。 */
    private double sceneMergeSeconds = 1.0;
    /** 单个视频关键帧上限（防止长视频 / 频繁切镜导致帧数失控）。 */
    private int maxKeyframes = 60;
    /** 抽帧输出宽度（像素），同一帧既上传为关键帧也用于 OCR。 */
    private int frameWidth = 1280;
    /** OCR 并行度（tesseract 进程数）。 */
    private int ocrParallelism = 4;

    public String getFfmpegPath() {
        return ffmpegPath;
    }

    public void setFfmpegPath(String ffmpegPath) {
        this.ffmpegPath = ffmpegPath;
    }

    public String getFfprobePath() {
        return ffprobePath;
    }

    public void setFfprobePath(String ffprobePath) {
        this.ffprobePath = ffprobePath;
    }

    public String getTesseractPath() {
        return tesseractPath;
    }

    public void setTesseractPath(String tesseractPath) {
        this.tesseractPath = tesseractPath;
    }

    public String getTesseractLanguages() {
        return tesseractLanguages;
    }

    public void setTesseractLanguages(String tesseractLanguages) {
        this.tesseractLanguages = tesseractLanguages;
    }

    public int getKeyframeCount() {
        return keyframeCount;
    }

    public void setKeyframeCount(int keyframeCount) {
        this.keyframeCount = keyframeCount;
    }

    public int getKeyframeIntervalSeconds() {
        return keyframeIntervalSeconds;
    }

    public void setKeyframeIntervalSeconds(int keyframeIntervalSeconds) {
        this.keyframeIntervalSeconds = keyframeIntervalSeconds;
    }

    public int getOcrFrameCount() {
        return ocrFrameCount;
    }

    public void setOcrFrameCount(int ocrFrameCount) {
        this.ocrFrameCount = ocrFrameCount;
    }

    public int getOcrFrameIntervalSeconds() {
        return ocrFrameIntervalSeconds;
    }

    public void setOcrFrameIntervalSeconds(int ocrFrameIntervalSeconds) {
        this.ocrFrameIntervalSeconds = ocrFrameIntervalSeconds;
    }

    public boolean isOcrEnabled() {
        return ocrEnabled;
    }

    public void setOcrEnabled(boolean ocrEnabled) {
        this.ocrEnabled = ocrEnabled;
    }

    public int getAnalysisWindowSeconds() {
        return analysisWindowSeconds;
    }

    public void setAnalysisWindowSeconds(int analysisWindowSeconds) {
        this.analysisWindowSeconds = analysisWindowSeconds;
    }

    public int getHookDenseSeconds() {
        return hookDenseSeconds;
    }

    public void setHookDenseSeconds(int hookDenseSeconds) {
        this.hookDenseSeconds = hookDenseSeconds;
    }

    public double getHookFrameIntervalSeconds() {
        return hookFrameIntervalSeconds;
    }

    public void setHookFrameIntervalSeconds(double hookFrameIntervalSeconds) {
        this.hookFrameIntervalSeconds = hookFrameIntervalSeconds;
    }

    public double getFrameIntervalSeconds() {
        return frameIntervalSeconds;
    }

    public void setFrameIntervalSeconds(double frameIntervalSeconds) {
        this.frameIntervalSeconds = frameIntervalSeconds;
    }

    public double getSceneThreshold() {
        return sceneThreshold;
    }

    public void setSceneThreshold(double sceneThreshold) {
        this.sceneThreshold = sceneThreshold;
    }

    public double getSceneMergeSeconds() {
        return sceneMergeSeconds;
    }

    public void setSceneMergeSeconds(double sceneMergeSeconds) {
        this.sceneMergeSeconds = sceneMergeSeconds;
    }

    public int getMaxKeyframes() {
        return maxKeyframes;
    }

    public void setMaxKeyframes(int maxKeyframes) {
        this.maxKeyframes = maxKeyframes;
    }

    public int getFrameWidth() {
        return frameWidth;
    }

    public void setFrameWidth(int frameWidth) {
        this.frameWidth = frameWidth;
    }

    public int getOcrParallelism() {
        return ocrParallelism;
    }

    public void setOcrParallelism(int ocrParallelism) {
        this.ocrParallelism = ocrParallelism;
    }
}
