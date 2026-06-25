import os

# 在 import 任何 app 模組前設定環境變數，
# 因為 config.config 在模組層級執行 Config = AppConfig(os.environ)
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("GITHUB_BOT_APP_ID", "12345")
os.environ.setdefault("GITHUB_BOT_PRIVATE_KEY_PATH", "/dev/null")
os.environ.setdefault("RUNNER_NAME_PREFIX", "test-runner")
os.environ.setdefault("RUNNER_SCOPE", "org")
os.environ.setdefault("ORG_NAME", "test-org")
os.environ.setdefault("DISABLE_AUTO_UPDATE", "true")
os.environ.setdefault("WEBHOOK_VERIFY", "false")
os.environ.setdefault("RUNNER_IMAGE", "ghcr.io/test/php-runner")
os.environ.setdefault("RUNNER_BASE_IMAGE", "myoung34/github-runner")
os.environ.setdefault("RUNNER_BASE_IMAGE_TAG", "ubuntu-noble")

import pytest


@pytest.fixture()
def env_config():
    """提供一組完整的測試用環境變數 dict。"""
    return {
        "WEBHOOK_VERIFY": "true",
        "GITHUB_WEBHOOK_SECRET": "test-secret",
        "VERIFY_SIGNATURE": "sha256",
        "GITHUB_BOT_APP_ID": "12345",
        "GITHUB_BOT_PRIVATE_KEY_PATH": "/tmp/test-key.pem",
        "RUNNER_NAME_PREFIX": "test-runner",
        "RUNNER_GROUP": "default",
        "RUNNER_SCOPE": "org",
        "ORG_NAME": "test-org",
        "DISABLE_AUTO_UPDATE": "true",
        "GITHUB_API_VERSION": "2022-11-28",
        "RUNNER_IMAGE": "ghcr.io/test/php-runner",
        "RUNNER_IMAGE_TAG": "8.4",
        "RUNNER_BASE_IMAGE": "myoung34/github-runner",
        "RUNNER_BASE_IMAGE_TAG": "ubuntu-noble",
    }
