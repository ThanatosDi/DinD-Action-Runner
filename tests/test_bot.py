import json
from unittest.mock import MagicMock, patch

import pytest
import requests

import bot as bot_module
from config.config import Config
from enums.headers import GithubWebhookHeaders


def _make_payload(action="queued", labels=None):
    """建立測試用的 webhook payload dict。"""
    if labels is None:
        labels = ["self-hosted", "linux"]
    return {
        "action": action,
        "installation": {"id": 99},
        "repository": {"name": "test-repo"},
        "workflow_job": {
            "labels": labels,
            "workflow_name": "CI",
            "name": "build",
        },
    }


@pytest.fixture()
def client():
    """建立測試用 Flask test client，mock 外部依賴。"""
    # Mock module-level bot object
    mock_bot = MagicMock()
    mock_access_token = MagicMock()
    mock_access_token.token = "fake-access-token"
    mock_bot.integration.get_access_token.return_value = mock_access_token
    mock_bot.get_self_hosted_runner_registration_token.return_value = {"token": "reg-token"}

    # Mock DynamicRunner
    mock_runner = MagicMock()
    mock_runner.image.return_value = "myoung34/github-runner:ubuntu-noble"
    mock_container = MagicMock()
    mock_container.short_id = "abc123"
    mock_runner.create.return_value = mock_container

    # Mock PEMFingerprint
    mock_pem = MagicMock()
    mock_pem.fingerprint = "test****print"

    with patch.object(bot_module, "bot", mock_bot), \
         patch.object(bot_module, "DynamicRunner", return_value=mock_runner), \
         patch.object(bot_module, "PEMFingerprint", return_value=mock_pem), \
         patch.object(Config, "WEBHOOK_VERIFY", False), \
         patch.object(Config, "GITHUB_BOT_APP_ID", "12345"), \
         patch.object(Config, "ORG_NAME", "test-org"):

        bot_module.app.config["TESTING"] = True
        yield bot_module.app.test_client()


class TestWebhookGet:
    """GET 端點測試"""

    def test_get_returns_200(self, client):
        """8.1.1 GET / 回傳 200 'OK, Bot'"""
        response = client.get("/")
        assert response.status_code == 200
        assert "OK, Bot" in response.get_json()


class TestWebhookPost:
    """POST 端點測試"""

    def test_non_integration_returns_401(self, client):
        """8.1.2 非 GitHub App 來源回傳 401"""
        payload = _make_payload()
        response = client.post(
            "/",
            data=json.dumps(payload),
            content_type="application/json",
            headers={
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "user",
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "99999",
            },
        )
        assert response.status_code == 401

    def test_empty_payload_returns_400(self, client):
        """8.1.3 空 payload 回傳 400"""
        response = client.post(
            "/",
            data=json.dumps({}),
            content_type="application/json",
            headers={
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "integration",
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "12345",
            },
        )
        assert response.status_code == 400

    def test_invalid_signature_returns_401(self, client):
        """8.1.4 啟用驗證且簽名無效回傳 401"""
        with patch.object(Config, "WEBHOOK_VERIFY", True), \
             patch.object(Config, "VERIFY_SIGNATURE", "sha256"), \
             patch.object(Config, "GITHUB_WEBHOOK_SECRET", "test-secret"):
            payload = _make_payload()
            body = json.dumps(payload).encode()
            response = client.post(
                "/",
                data=body,
                content_type="application/json",
                headers={
                    GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "integration",
                    GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "12345",
                    "X-Hub-Signature-256": "sha256=" + "0" * 64,
                },
            )
            assert response.status_code == 401

    def test_non_queued_returns_200(self, client):
        """8.1.5 非 queued 事件回傳 200"""
        payload = _make_payload(action="completed")
        response = client.post(
            "/",
            data=json.dumps(payload),
            content_type="application/json",
            headers={
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "integration",
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "12345",
            },
        )
        assert response.status_code == 200

    def test_no_labels_returns_400(self, client):
        """8.1.6 無 labels 回傳 400"""
        payload = _make_payload(labels=[])
        response = client.post(
            "/",
            data=json.dumps(payload),
            content_type="application/json",
            headers={
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "integration",
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "12345",
            },
        )
        assert response.status_code == 400

    def test_no_self_hosted_label_returns_400(self, client):
        """8.1.7 無 self-hosted label 回傳 400"""
        payload = _make_payload(labels=["linux", "x64"])
        response = client.post(
            "/",
            data=json.dumps(payload),
            content_type="application/json",
            headers={
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "integration",
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "12345",
            },
        )
        assert response.status_code == 400

    def test_successful_runner_creation(self, client):
        """8.1.8 成功建立 runner 回傳 200 及完整訊息"""
        payload = _make_payload()
        response = client.post(
            "/",
            data=json.dumps(payload),
            content_type="application/json",
            headers={
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "integration",
                GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "12345",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "Image" in data
        assert "Labels" in data
        assert "Repository" in data
        assert "Workflow Name" in data
        assert "Job" in data
        assert "Container Name" in data

    def test_registration_token_failure_returns_500(self):
        """8.1.9 取得 registration token 失敗回傳 500"""
        mock_bot = MagicMock()
        mock_access_token = MagicMock()
        mock_access_token.token = "fake-token"
        mock_bot.integration.get_access_token.return_value = mock_access_token
        mock_bot.get_self_hosted_runner_registration_token.side_effect = requests.HTTPError("500")

        mock_runner = MagicMock()
        mock_runner.image.return_value = "test:latest"

        mock_pem = MagicMock()
        mock_pem.fingerprint = "test****print"

        with patch.object(bot_module, "bot", mock_bot), \
             patch.object(bot_module, "DynamicRunner", return_value=mock_runner), \
             patch.object(bot_module, "PEMFingerprint", return_value=mock_pem), \
             patch.object(Config, "WEBHOOK_VERIFY", False), \
             patch.object(Config, "GITHUB_BOT_APP_ID", "12345"), \
             patch.object(Config, "ORG_NAME", "test-org"):

            bot_module.app.config["TESTING"] = True
            test_client = bot_module.app.test_client()

            payload = _make_payload()
            response = test_client.post(
                "/",
                data=json.dumps(payload),
                content_type="application/json",
                headers={
                    GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value: "integration",
                    GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value: "12345",
                },
            )
            assert response.status_code == 500
