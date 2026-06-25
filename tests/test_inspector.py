from unittest.mock import patch

from app.inspector import Inspector
from config.config import Config
from enums.headers import GithubWebhookHeaders


class TestInspector:
    """Inspector 單元測試"""

    def test_is_integration_returns_true(self):
        """4.1.1 target_type 為 'integration' 且 target_id 匹配時回傳 True"""
        with patch.object(Config, "GITHUB_BOT_APP_ID", "12345"):
            inspector = Inspector()
            headers = {
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "integration",
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "12345",
            }
            assert inspector.is_integration(headers) is True

    def test_wrong_target_type_returns_false(self):
        """4.1.2 target_type 不是 'integration' 時回傳 False"""
        with patch.object(Config, "GITHUB_BOT_APP_ID", "12345"):
            inspector = Inspector()
            headers = {
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "user",
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "12345",
            }
            assert inspector.is_integration(headers) is False

    def test_wrong_target_id_returns_false(self):
        """4.1.3 target_id 不匹配時回傳 False"""
        with patch.object(Config, "GITHUB_BOT_APP_ID", "12345"):
            inspector = Inspector()
            headers = {
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "integration",
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "99999",
            }
            assert inspector.is_integration(headers) is False

    def test_missing_headers_returns_false(self):
        """4.1.4 headers 中缺少對應欄位時回傳 False"""
        with patch.object(Config, "GITHUB_BOT_APP_ID", "12345"):
            inspector = Inspector()
            assert inspector.is_integration({}) is False
