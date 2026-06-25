import re
import uuid

import docker
from config.config import Config

RUNNERS_WORK_BASE = "/runners-work"


class DynamicRunner:
    def __init__(self):
        self.docker = docker.from_env()

    def image(self, labels: list[str] | str) -> str:
        if isinstance(labels, str):
            labels = labels.split(",")
        php_version = next(
            (label for label in labels if re.match(r"php\d", label)), None
        )
        if php_version is None:
            return f"{Config.RUNNER_BASE_IMAGE}:{Config.RUNNER_BASE_IMAGE_TAG}"
        php_version_number = php_version.replace("php", "")
        return f"{Config.RUNNER_IMAGE}:{php_version_number}"

    def _build_volumes(self) -> list[str]:
        """建構 runner 容器的 volume 掛載清單。

        使用 bind mount（/ 開頭）而非 named volume：
        named volume 由 DinD daemon 管理，與 compose 的 Host daemon volume 是不同 storage；
        bind mount 直接掛載 DinD container 的 filesystem（Host volume 掛載點）。
        """
        return [
            "/var/run/docker.sock:/var/run/docker.sock",
            f"{RUNNERS_WORK_BASE}:{RUNNERS_WORK_BASE}",
            "/actions-runner/externals:/actions-runner/externals",
            "/app/hooks:/hooks:ro",
        ]

    def _build_environment(self, registration_token: str, labels: str, workdir: str) -> dict[str, str]:
        """建構容器環境變數。"""
        return {
            "RUNNER_TOKEN": registration_token,
            "RUNNER_NAME_PREFIX": Config.RUNNER_NAME_PREFIX,
            "RUNNER_WORKDIR": workdir,
            "RUNNER_GROUP": Config.RUNNER_GROUP,
            "RUNNER_SCOPE": Config.RUNNER_SCOPE,
            "ORG_NAME": Config.ORG_NAME,
            "DISABLE_AUTO_UPDATE": Config.DISABLE_AUTO_UPDATE,
            "LABELS": labels,
            "EPHEMERAL": "1",
            "ACTIONS_RUNNER_HOOK_JOB_COMPLETED": "/hooks/job-completed.sh",
        }

    def create(self, image: str, labels: str, registration_token: str):
        runner_id = uuid.uuid4().hex[:8]
        workdir = f"{RUNNERS_WORK_BASE}/{runner_id}"

        return self.docker.containers.run(
            image,
            detach=True,
            auto_remove=True,
            environment=self._build_environment(registration_token, labels, workdir),
            volumes=self._build_volumes(),
            network="github-action",
        )

    def cleanup_volume(self, volume_name: str) -> None:
        """移除指定的 Docker named volume。"""
        try:
            volume = self.docker.volumes.get(volume_name)
            volume.remove()
        except docker.errors.NotFound:
            pass
