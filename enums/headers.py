from enum import Enum


class GithubWebhookHeaders(Enum):
    GITHUB_WEBHOOK_TARGET_ID = 'X-GitHub-Hook-Installation-Target-ID'
    GITHUB_WEBHOOK_TARGET_TYPE = 'X-GitHub-Hook-Installation-Target-Type'
    GITHUB_WEBHOOK_EVENT = 'X-GitHub-Event'