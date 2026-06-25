from unittest.mock import MagicMock, patch

import pytest

from config.config import Config


@pytest.fixture()
def mock_docker():
    with patch("app.dynamic_runner.docker.from_env") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture()
def _mock_config():
    """Mock Config 上 DynamicRunner 使用的所有欄位。"""
    with patch.object(Config, "RUNNER_IMAGE", "ghcr.io/test/php-runner"), \
         patch.object(Config, "RUNNER_BASE_IMAGE", "myoung34/github-runner"), \
         patch.object(Config, "RUNNER_BASE_IMAGE_TAG", "ubuntu-noble"), \
         patch.object(Config, "RUNNER_NAME_PREFIX", "test-runner"), \
         patch.object(Config, "RUNNER_GROUP", "default"), \
         patch.object(Config, "RUNNER_SCOPE", "org"), \
         patch.object(Config, "ORG_NAME", "test-org"), \
         patch.object(Config, "DISABLE_AUTO_UPDATE", "true"):
        yield


@pytest.mark.usefixtures("_mock_config")
class TestDynamicRunnerImage:
    """DynamicRunner.image() 測試"""

    def test_php_label_returns_php_image(self, mock_docker):
        """7.1.1 labels 包含 'php84' 時回傳對應 PHP 映像"""
        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        result = runner.image(["self-hosted", "php84"])
        assert result == "ghcr.io/test/php-runner:84"

    def test_no_php_label_returns_base_image(self, mock_docker):
        """7.1.2 labels 不含 PHP 版本時回傳基礎映像"""
        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        result = runner.image(["self-hosted", "linux"])
        assert result == "myoung34/github-runner:ubuntu-noble"

    def test_string_labels_split_correctly(self, mock_docker):
        """7.1.3 labels 為逗號分隔字串時正確拆分"""
        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        result = runner.image("self-hosted,php82")
        assert result == "ghcr.io/test/php-runner:82"


@pytest.mark.usefixtures("_mock_config")
class TestDynamicRunnerCreate:
    """DynamicRunner.create() 測試"""

    def test_create_calls_docker_with_correct_params(self, mock_docker):
        """7.1.4 create 方法以正確參數呼叫 docker SDK"""
        mock_docker.containers.run.return_value = MagicMock(short_id="abc123")

        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        runner.create("test-image:latest", "self-hosted,linux", "reg-token-123")

        mock_docker.containers.run.assert_called_once()
        call_args = mock_docker.containers.run.call_args
        assert call_args[0][0] == "test-image:latest"
        assert call_args[1]["detach"] is True

    def test_container_env_vars(self, mock_docker):
        """7.1.5 容器環境變數包含所有必要設定"""
        mock_docker.containers.run.return_value = MagicMock(short_id="abc123")

        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        runner.create("test-image:latest", "self-hosted", "reg-token-123")

        call_args = mock_docker.containers.run.call_args
        env = call_args[1]["environment"]
        assert env["RUNNER_TOKEN"] == "reg-token-123"
        assert env["RUNNER_NAME_PREFIX"] == "test-runner"
        assert env["RUNNER_WORKDIR"].startswith("/runners-work/")
        assert env["RUNNER_GROUP"] == "default"
        assert env["RUNNER_SCOPE"] == "org"
        assert env["ORG_NAME"] == "test-org"
        assert env["LABELS"] == "self-hosted"
        assert env["EPHEMERAL"] == "1"


@pytest.mark.usefixtures("_mock_config")
class TestDynamicRunnerContainerVolume:
    """DynamicRunner volume 與 workdir 策略測試（統一配置）"""

    def test_shared_volume_and_externals_mounted(self, mock_docker):
        """掛載共享 runners-work 和 runner-externals volume"""
        mock_docker.containers.run.return_value = MagicMock(short_id="abc123")

        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        runner.create("test-image:latest", "self-hosted", "reg-token-123")

        call_args = mock_docker.containers.run.call_args
        volumes = call_args[1]["volumes"]
        assert "/runners-work:/runners-work" in volumes
        assert "/actions-runner/externals:/actions-runner/externals" in volumes

    def test_workdir_is_unique(self, mock_docker):
        """每個 runner 的 RUNNER_WORKDIR 使用唯一子目錄"""
        mock_docker.containers.run.return_value = MagicMock(short_id="abc123")

        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        runner.create("test-image:latest", "self-hosted", "reg-token-123")
        workdir_1 = mock_docker.containers.run.call_args[1]["environment"]["RUNNER_WORKDIR"]

        runner.create("test-image:latest", "self-hosted", "reg-token-456")
        workdir_2 = mock_docker.containers.run.call_args[1]["environment"]["RUNNER_WORKDIR"]

        assert workdir_1.startswith("/runners-work/")
        assert workdir_2.startswith("/runners-work/")
        assert workdir_1 != workdir_2

    def test_runners_work_always_mounted(self, mock_docker):
        """runner container 一律掛載 runners-work、externals、hooks"""
        mock_docker.containers.run.return_value = MagicMock(short_id="abc123")

        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        runner.create("test-image:latest", "self-hosted", "reg-token-123")

        call_args = mock_docker.containers.run.call_args
        volumes = call_args[1]["volumes"]
        assert "/runners-work:/runners-work" in volumes
        assert "/actions-runner/externals:/actions-runner/externals" in volumes
        assert "/app/hooks:/hooks:ro" in volumes

    def test_job_completed_hook_env_set(self, mock_docker):
        """ACTIONS_RUNNER_HOOK_JOB_COMPLETED 無條件被設定"""
        mock_docker.containers.run.return_value = MagicMock(short_id="abc123")

        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        runner.create("test-image:latest", "self-hosted", "reg-token-123")

        call_args = mock_docker.containers.run.call_args
        env = call_args[1]["environment"]
        assert env["ACTIONS_RUNNER_HOOK_JOB_COMPLETED"] == "/hooks/job-completed.sh"

    def test_docker_socket_always_mounted(self, mock_docker):
        """Docker socket 永遠掛載"""
        mock_docker.containers.run.return_value = MagicMock(short_id="abc123")

        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        runner.create("test-image:latest", "self-hosted", "reg-token-123")

        call_args = mock_docker.containers.run.call_args
        volumes = call_args[1]["volumes"]
        socket_mount = [v for v in volumes if "docker.sock" in v]
        assert len(socket_mount) == 1


class TestCleanupVolume:
    """Volume 清理機制測試"""

    def test_cleanup_volume_removes_volume(self, mock_docker):
        """4.1.1 cleanup_volume 呼叫 Docker SDK 移除指定 volume"""
        mock_volume = MagicMock()
        mock_docker.volumes.get.return_value = mock_volume

        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        runner.cleanup_volume("runner-abc-work")

        mock_docker.volumes.get.assert_called_once_with("runner-abc-work")
        mock_volume.remove.assert_called_once()

    def test_cleanup_volume_not_found_silent(self, mock_docker):
        """4.1.2 volume 不存在時不拋錯"""
        import docker as docker_lib
        mock_docker.volumes.get.side_effect = docker_lib.errors.NotFound("not found")

        from app.dynamic_runner import DynamicRunner
        runner = DynamicRunner()
        runner.cleanup_volume("nonexistent-volume")  # 不應拋出例外
