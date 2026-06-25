import tempfile
from unittest.mock import patch

import pytest
from OpenSSL import crypto

from app.pem_fingerprint import PEMFingerprint
from config.config import Config


@pytest.fixture()
def tmp_pem_file():
    """建立一個暫時的 PEM 私鑰檔案。"""
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    pem_data = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as f:
        f.write(pem_data)
        return f.name


class TestPEMFingerprint:
    """PEMFingerprint 單元測試"""

    def test_valid_pem_returns_masked_fingerprint(self, tmp_pem_file):
        """5.1.1 提供有效 PEM 路徑時回傳遮罩後的指紋字串"""
        with patch.object(Config, "GITHUB_BOT_PRIVATE_KEY_PATH", tmp_pem_file):
            fp = PEMFingerprint()
            result = fp.fingerprint
            assert result is not None
            assert "*" in result

    def test_empty_path_returns_none(self):
        """5.1.2 路徑為空字串時回傳 None"""
        with patch.object(Config, "GITHUB_BOT_PRIVATE_KEY_PATH", ""):
            fp = PEMFingerprint()
            assert fp.fingerprint is None

    def test_nonexistent_file_returns_none(self):
        """5.1.3 檔案不存在時回傳 None"""
        with patch.object(Config, "GITHUB_BOT_PRIVATE_KEY_PATH", "/tmp/nonexistent_key_12345.pem"):
            fp = PEMFingerprint()
            assert fp.fingerprint is None

    def test_hide_text_default_char(self):
        """5.1.4 hide_text 使用預設遮罩字元 *"""
        fp = PEMFingerprint()
        result = fp.hide_text("ABCDEFGHIJ")
        assert "*" in result

    def test_hide_text_custom_char(self):
        """5.1.5 hide_text 使用自訂遮罩字元"""
        fp = PEMFingerprint()
        result = fp.hide_text("ABCDEFGHIJ", replace_char="#")
        assert "#" in result
        assert "*" not in result
