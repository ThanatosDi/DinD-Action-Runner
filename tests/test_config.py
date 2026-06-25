import pytest

from config.config import AppConfig, AppConfigError


class TestAppConfig:
    """AppConfig 單元測試"""

    def test_all_required_fields_set(self, env_config):
        """2.1.1 所有必填欄位皆設定時，成功建立 AppConfig"""
        config = AppConfig(env_config)
        assert config.ORG_NAME == "test-org"
        assert config.GITHUB_BOT_APP_ID == "12345"
        assert config.RUNNER_NAME_PREFIX == "test-runner"
        assert config.RUNNER_SCOPE == "org"

    def test_missing_required_field_raises_error(self):
        """2.1.2 缺少必填欄位時，拋出 AppConfigError"""
        env = {"WEBHOOK_VERIFY": "false"}
        with pytest.raises(AppConfigError, match="GITHUB_WEBHOOK_SECRET"):
            AppConfig(env)

    def test_bool_true_values(self):
        """2.1.3 布林值 'true'/'yes'/'1' 轉換為 True"""
        base = {
            "GITHUB_WEBHOOK_SECRET": "s",
            "GITHUB_BOT_APP_ID": "1",
            "GITHUB_BOT_PRIVATE_KEY_PATH": "/tmp/k.pem",
            "RUNNER_NAME_PREFIX": "r",
            "RUNNER_SCOPE": "org",
            "ORG_NAME": "o",
            "DISABLE_AUTO_UPDATE": "true",
        }
        for val in ["true", "True", "TRUE", "yes", "Yes", "1"]:
            env = {**base, "WEBHOOK_VERIFY": val}
            config = AppConfig(env)
            assert config.WEBHOOK_VERIFY is True, f"'{val}' should parse to True"

    def test_bool_false_values(self):
        """2.1.4 布林值 'false'/'no'/'0' 轉換為 False"""
        base = {
            "GITHUB_WEBHOOK_SECRET": "s",
            "GITHUB_BOT_APP_ID": "1",
            "GITHUB_BOT_PRIVATE_KEY_PATH": "/tmp/k.pem",
            "RUNNER_NAME_PREFIX": "r",
            "RUNNER_SCOPE": "org",
            "ORG_NAME": "o",
            "DISABLE_AUTO_UPDATE": "true",
        }
        for val in ["false", "False", "no", "0"]:
            env = {**base, "WEBHOOK_VERIFY": val}
            config = AppConfig(env)
            assert config.WEBHOOK_VERIFY is False, f"'{val}' should parse to False"

    def test_type_cast_mechanism(self, env_config):
        """2.1.5 型別轉換機制正常運作"""
        config = AppConfig(env_config)
        assert isinstance(config.GITHUB_WEBHOOK_SECRET, str)
        assert isinstance(config.WEBHOOK_VERIFY, bool)

    def test_default_values_used(self):
        """2.1.6 未設定的欄位使用預設值"""
        env = {
            "GITHUB_WEBHOOK_SECRET": "secret",
            "GITHUB_BOT_APP_ID": "1",
            "GITHUB_BOT_PRIVATE_KEY_PATH": "/tmp/k.pem",
            "RUNNER_NAME_PREFIX": "r",
            "RUNNER_SCOPE": "org",
            "ORG_NAME": "o",
            "DISABLE_AUTO_UPDATE": "true",
        }
        config = AppConfig(env)
        assert config.WEBHOOK_VERIFY is False
        assert config.VERIFY_SIGNATURE == "sha1"
        assert config.RUNNER_GROUP == "default"
        assert config.GITHUB_API_VERSION == "2022-11-28"
