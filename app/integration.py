from pathlib import Path

import requests
from github import GithubIntegration


class Integration(GithubIntegration):
    API_ENDPOINT: str = "https://api.github.com"
    API_VERSION: str = "2022-11-28"

    def __init__(self, app_id: str, app_key_path: Path | str):
        self.app_id = app_id
        self.__app_key = self.__read_private_key_as_str(app_key_path)

    def __read_private_key_as_str(self, app_key_path: Path | str) -> str | None:
        path = Path(app_key_path) if isinstance(app_key_path, str) else app_key_path
        if not path.exists():
            return None
        with open(path, "r") as fio:
            return fio.read()

    @property
    def integration(self):
        return GithubIntegration(self.app_id, self.__app_key)

    def get_self_hosted_runner_registration_token(
        self, access_token: str, org_name: str
    ) -> dict | requests.HTTPError:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": self.API_VERSION,
        }
        with requests.post(
            f"{self.API_ENDPOINT}/orgs/{org_name}/actions/runners/registration-token",
            headers=headers,
        ) as response:
            if response.status_code != 201:
                response.raise_for_status()
            return response.json()
