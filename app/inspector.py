from config.config import Config
from enums.headers import GithubWebhookHeaders


class Inspector():
    def __init__(self): ...

    def is_integration(self, headers: dict) -> bool:
        """
        檢查從 Github 來的請求是否為 Github App 所發送的

        Args:
            headers (dict): 請求的 headers。

        Returns:
            bool: 如果為 Github App 所發送，則為 True，否則為 False。
        """
        target_type = headers.get(
            GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_TYPE.value, '')
        target_id = headers.get(
            GithubWebhookHeaders.GITHUB_WEBHOOK_TARGET_ID.value, '')
        return target_type == 'integration' and target_id == Config.GITHUB_BOT_APP_ID
