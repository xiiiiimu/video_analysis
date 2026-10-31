package com.videodiagnosis.interfaces.controller;

import com.videodiagnosis.types.common.VideoDiagnosisException;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;

import java.nio.charset.StandardCharsets;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * 评分标准 txt 上传：UTF-8（含 Windows 记事本的 BOM）正常读取，空文件 / 非文本 / 超长拒绝。
 */
class CriteriaUploadTest {

    private static MockMultipartFile file(byte[] bytes) {
        return new MockMultipartFile("criteria", "标准.txt", "text/plain", bytes);
    }

    @Test
    void readsUtf8TextAndStripsBom() {
        byte[] bom = {(byte) 0xEF, (byte) 0xBB, (byte) 0xBF};
        byte[] body = "1. 开头3秒内说出卖点\n2. 不要出现竞品名字".getBytes(StandardCharsets.UTF_8);
        byte[] bytes = new byte[bom.length + body.length];
        System.arraycopy(bom, 0, bytes, 0, bom.length);
        System.arraycopy(body, 0, bytes, bom.length, body.length);

        assertThat(AnalysisCommandController.readCriteria(file(bytes))).startsWith("1. 开头3秒内说出卖点");
    }

    @Test
    void rejectsEmptyBinaryAndTooLongFiles() {
        assertThatThrownBy(() -> AnalysisCommandController.readCriteria(file(new byte[0])))
                .isInstanceOf(VideoDiagnosisException.class);
        assertThatThrownBy(() -> AnalysisCommandController.readCriteria(file(new byte[] {0x00, 0x01, (byte) 0xFF})))
                .isInstanceOf(VideoDiagnosisException.class);
        assertThatThrownBy(() -> AnalysisCommandController.readCriteria(file("长".repeat(20001).getBytes(StandardCharsets.UTF_8))))
                .isInstanceOf(VideoDiagnosisException.class);
    }
}
