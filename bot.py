import json
from pathlib import Path
from types import SimpleNamespace

import requests
from flask import Flask, request
from flask_restful import Api, Resource
from loguru import logger

from app.dynamic_runner import DynamicRunner
from app.inspector import Inspector
from app.integration import Integration
from app.pem_fingerprint import PEMFingerprint
from app.validate_signature import ValidateSignature
from config.config import Config

app = Flask(__name__)
webhook = Api(app)
bot = Integration(
    app_id=Config.GITHUB_BOT_APP_ID,
    app_key_path=Path(Config.GITHUB_BOT_PRIVATE_KEY_PATH),
)
bot.API_VERSION = Config.GITHUB_API_VERSION


class GithubBotResource(Resource, ValidateSignature):
    def get(self):
        return "OK, Bot", 200

    def post(self):
        logger.info(f"Use PEM Fingerprint: {PEMFingerprint().fingerprint}")
        payload = json.loads(
            request.get_data(as_text=True), object_hook=lambda d: SimpleNamespace(**d)
        )

        if Inspector().is_integration(request.headers) is False:
            logger.error("ERROR: Request is not from Github App")
            return "Request is not from Github App", 401

        if not any(request.get_json()):
            logger.error("ERROR: No payload in request")
            return "No payload in request", 400

        if Config.WEBHOOK_VERIFY:
            match Config.VERIFY_SIGNATURE:
                case "sha1":
                    verify = super().sha1(request, Config.GITHUB_WEBHOOK_SECRET)
                case "sha256":
                    verify = super().sha256(request, Config.GITHUB_WEBHOOK_SECRET)
                case _:
                    logger.error("ERROR: VERIFY_SIGNATURE must be sha1 or sha256")
                    raise ValueError("VERIFY_SIGNATURE must be sha1 or sha256")
            if verify is False:
                logger.error("ERROR: Invalid signature")
                return "Invalid signature", 401

        if payload.action != "queued":
            logger.info("Event is not queued, still return 200 but do not anything.")
            return "Event is not queued", 200

        if not any(payload.workflow_job.labels):
            logger.error("ERROR: No labels in workflow_job")
            return "No labels in workflow_job", 400

        if "self-hosted" not in payload.workflow_job.labels:
            logger.error("ERROR: No self-hosted in labels")
            return "No self-hosted in labels", 400

        installation_id = payload.installation.id
        labels = ",".join(payload.workflow_job.labels)
        repository = payload.repository.name
        workflow_name = payload.workflow_job.workflow_name
        job = payload.workflow_job.name
        # image = DynamicRunner().image(payload.workflow_job.labels)
        image = f"{Config.RUNNER_BASE_IMAGE}:{Config.RUNNER_BASE_IMAGE_TAG}"

        logger.info(
            f"Event: {payload.action}, installation_id: {installation_id}, "
            f"labels: {labels}, repository: {repository}, "
            f"workflow_name: {workflow_name}, job: {job}"
        )

        token = bot.integration.get_access_token(installation_id).token
        try:
            registration_token = bot.get_self_hosted_runner_registration_token(
                token, Config.ORG_NAME
            )
        except requests.HTTPError as e:
            logger.error(e)
            return "Get self-hosted runner registration token error", 500

        container = DynamicRunner().create(image, labels, registration_token["token"])
        message = {
            "Image": image,
            "Labels": labels,
            "Repository": repository,
            "Workflow Name": workflow_name,
            "Job": job,
            "Container Name": container.short_id,
        }
        logger.info(message)
        return message, 200


webhook.add_resource(GithubBotResource, "/")

if __name__ == "__main__":
    app.run(debug=False, port=80, host="0.0.0.0")
