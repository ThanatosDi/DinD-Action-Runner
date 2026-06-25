import tempfile
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.integration import Integration


@pytest.fixture()
def tmp_key_file():
    """建立一個暫時的私鑰檔案。"""
    content = "-----BEGIN RSA PRIVATE KEY-----\nfake-key-content\n-----END RSA PRIVATE KEY-----"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
        f.write(content)
        return f.name


class TestIntegrationInit:
    """Integration 初始化測試"""

    def test_read_key_file_exists(self, tmp_key_file):
        """6.1.1 私鑰檔案存在時成功讀取"""
        integration = Integration(app_id="123", app_key_path=tmp_key_file)
        assert integration._Integration__app_key is not None
        assert "fake-key-content" in integration._Integration__app_key

    def test_read_key_file_not_exists(self):
        """6.1.2 私鑰檔案不存在時設為 None"""
        integration = Integration(app_id="123", app_key_path="/tmp/nonexistent_key_99999.pem")
        assert integration._Integration__app_key is None

    def test_string_path_converted(self, tmp_key_file):
        """6.1.3 路徑為字串時自動轉換為 Path"""
        integration = Integration(app_id="123", app_key_path=tmp_key_file)
        assert integration._Integration__app_key is not None

    def test_integration_property(self, tmp_key_file):
        """6.1.4 integration 屬性回傳 GithubIntegration 實例"""
        from github import GithubIntegration as GI
        integration = Integration(app_id="123", app_key_path=tmp_key_file)
        result = integration.integration
        assert isinstance(result, GI)


class TestRegistrationToken:
    """Registration token 取得測試"""

    def test_successful_token_retrieval(self, tmp_key_file):
        """6.1.5 成功取得 registration token"""
        integration = Integration(app_id="123", app_key_path=tmp_key_file)

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"token": "test-reg-token"}
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("app.integration.requests.post", return_value=mock_response):
            result = integration.get_self_hosted_runner_registration_token(
                "fake-access-token", "test-org"
            )
            assert result == {"token": "test-reg-token"}

    def test_api_error_raises_http_error(self, tmp_key_file):
        """6.1.6 API 回傳非 201 時拋出 HTTPError"""
        integration = Integration(app_id="123", app_key_path=tmp_key_file)

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("app.integration.requests.post", return_value=mock_response):
            with pytest.raises(requests.HTTPError):
                integration.get_self_hosted_runner_registration_token(
                    "fake-access-token", "test-org"
                )
