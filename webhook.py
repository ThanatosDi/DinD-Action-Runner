import hashlib
import hmac

from flask import Flask, Request, request
from flask_restful import Api, Resource

import docker
from config.config import Config

app = Flask(__name__)
webhook = Api(app)


class ValidateSignature():
    def preprocessing(self, request: Request) -> tuple[str, str]:
        signature_header = request.headers['X-Hub-Signature']
        sha_name, github_signature = signature_header.split('=')
        body = request.get_data()
        return (sha_name, github_signature, body)

    def sha1(self, request: Request, secret: str):
        sha_name, github_signature, body = self.preprocessing(request)
        if sha_name != 'sha1':
            print('ERROR: X-Hub-Signature in payload headers was not sha1=****')
            return False

        # Create our own signature
        local_signature = hmac.new(secret.encode(
            'utf-8'), msg=body, digestmod=hashlib.sha1)

        # See if they match
        return hmac.compare_digest(local_signature.hexdigest(), github_signature)

    def sha256(self, request: Request, secret: str):
        sha_name, github_signature, body = self.preprocessing(request)
        if sha_name != 'sha256':
            print('ERROR: X-Hub-Signature in payload headers was not sha256=****')
            return False

        # Create our own signature
        local_signature = hmac.new(secret.encode(
            'utf-8'), msg=body, digestmod=hashlib.sha256)

        # See if they match
        return hmac.compare_digest(local_signature.hexdigest(), github_signature)


class DynamicRunner():
    def __init__(self):
        # self.docker = docker.DockerClient(
        #     base_url='unix://var/run/docker.sock')
        self.docker = docker.from_env()

    def create(self, labels: str):
        self.docker.containers.run(
            'myoung34/github-runner:latest',
            detach=True,
            auto_remove=True,
            environment={
                'ACCESS_TOKEN': Config.GITHUB_ACCESS_TOKEN,
                'RUNNER_NAME_PREFIX': Config.RUNNER_NAME_PREFIX,
                'RUNNER_WORKDIR': Config.RUNNER_WORKDIR,
                'RUNNER_GROUP': Config.RUNNER_GROUP,
                'RUNNER_SCOPE': Config.RUNNER_SCOPE,
                'ORG_NAME': Config.ORG_NAME,
                'DISABLE_AUTO_UPDATE': Config.DISABLE_AUTO_UPDATE,
                'LABELS': labels,
                'EPHEMERAL': 1,
            },
            volumes=[
                '/var/run/docker.sock:/var/run/docker.sock',
            ],
            network='github-action'
        )


class GithubEvent(Resource, ValidateSignature):
    def __init__(self): ...

    def get(self):
        return 'OK', 200

    def post(self):
        payload: dict = request.get_json()
        if super().sha1(request, '0000') == False:
            print('ERROR: Invalid signature')
            return 'Invalid signature', 401
        if not payload:
            print('ERROR: No payload in request')
            return 'No payload in request', 400
        if not payload.get('action') == 'queued':
            print('ERROR: Event was not queued')
            return 'Event was not queued', 400
        if not payload['workflow_job'].get('labels'):
            print('ERROR: No labels in workflow_job')
            return 'No labels in workflow_job', 400
        labels = ','.join(payload['workflow_job']['labels'])
        DynamicRunner().create(labels)


webhook.add_resource(GithubEvent, '/')

if __name__ == '__main__':
    app.run(debug=False, port=80, host='0.0.0.0')