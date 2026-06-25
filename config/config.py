import os
from typing import Union, get_type_hints

from dotenv import load_dotenv

load_dotenv(override=True)


class AppConfigError(Exception):
    pass


def _parse_bool(val: Union[str, bool]) -> bool:
    return val if isinstance(val, bool) else val.lower() in ['true', 'yes', '1']


class AppConfig:
    WEBHOOK_VERIFY: bool = False
    GITHUB_WEBHOOK_SECRET: str
    VERIFY_SIGNATURE: str = 'sha1'
    GITHUB_BOT_APP_ID: str
    GITHUB_BOT_PRIVATE_KEY_PATH: str
    RUNNER_NAME_PREFIX: str
    RUNNER_GROUP: str = 'default'
    RUNNER_SCOPE: str
    ORG_NAME: str
    DISABLE_AUTO_UPDATE: str
    GITHUB_API_VERSION: str = '2022-11-28'
    RUNNER_IMAGE: str = 'ghcr.io/your-org/your-runner'
    RUNNER_IMAGE_TAG: str = 'latest'
    RUNNER_BASE_IMAGE: str = 'myoung34/github-runner'
    RUNNER_BASE_IMAGE_TAG: str = 'ubuntu-noble'

    def __init__(self, env):
        hints = get_type_hints(type(self))
        for field, var_type in hints.items():
            if not field.isupper():
                continue

            default_value = getattr(type(self), field, None)
            if default_value is None and env.get(field) is None:
                raise AppConfigError(
                    f'The "{field}" field is required but was not provided'
                )

            raw_value = env.get(field, default_value)
            setattr(self, field, self._cast_field(field, var_type, raw_value))

    def _cast_field(self, field: str, var_type: type, raw_value):
        """將原始值轉換為目標型別。"""
        try:
            if var_type is bool:
                return _parse_bool(raw_value)
            return var_type(raw_value)
        except ValueError:
            raise AppConfigError(
                f'Unable to cast value "{raw_value}" to type "{var_type.__name__}" '
                f'for field "{field}"'
            )

    def __repr__(self):
        return str(self.__dict__)


# Expose Config object for app to import
Config = AppConfig(os.environ)
