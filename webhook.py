import hashlib
import hmac

from flask import Flask, Request, request
from flask_restful import Api, Resource

import docker
from config.config import Config

app = Flask(__name__)
webhook = Api(app)


class ValidateSignature():
    def preprocessing(self, request: Request, signature: str) -> tuple[str, str]:
        match(signature):
            case 'sha1':
                signature_header_name = 'X-Hub-Signature'
            case 'sha256':
                signature_header_name = 'X-Hub-Signature-256'
        signature_header = request.headers[signature_header_name]
        print(signature_header)
        sha_name, github_signature = signature_header.split('=')
        body = request.get_data()
        return (sha_name, github_signature, body)

    def sha1(self, request: Request, secret: str) -> bool:
        sha_name, github_signature, body = self.preprocessing(request, 'sha1')
        if sha_name != 'sha1':
            print('ERROR: X-Hub-Signature in payload headers was not sha1=****')
            return False

        # Create our own signature
        local_signature = hmac.new(secret.encode(
            'utf-8'), msg=body, digestmod=hashlib.sha1)

        # See if they match
        return hmac.compare_digest(local_signature.hexdigest(), github_signature)

    def sha256(self, request: Request, secret: str) -> bool:
        sha_name, github_signature, body = self.preprocessing(request, 'sha256')
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
    def __init__(self):
        if Config.WEBHOOK_VERIFY and (Config.VERIFY_SIGNATURE not in ['sha1', 'sha256']):
            raise ValueError('VERIFY_SIGNATURE must be sha1 or sha256')

    def get(self):
        return 'OK', 200

    def post(self):
        payload: dict = request.get_json()
        if not payload:
            print('ERROR: No payload in request')
            return 'No payload in request', 400

        if Config.WEBHOOK_VERIFY:
            match(Config.VERIFY_SIGNATURE):
                case 'sha1':
                    verify = super().sha1(request, Config.GITHUB_WEBHOOK_SECRET)
                case 'sha256':
                    verify = super().sha256(request, Config.GITHUB_WEBHOOK_SECRET)
                case _:
                    raise ValueError('VERIFY_SIGNATURE must be sha1 or sha256')
            if verify == False:
                print('ERROR: Invalid signature')
                return 'Invalid signature', 401

        if not payload.get('action') == 'queued':
            print('ERROR: Event was not queued, still return 200 but do not things.')
            return 'Event was not queued', 200

        if not payload['workflow_job'].get('labels'):
            print('ERROR: No labels in workflow_job')
            return 'No labels in workflow_job', 400

        labels = ','.join(payload['workflow_job']['labels'])
        DynamicRunner().create(labels)


webhook.add_resource(GithubEvent, '/')

if __name__ == '__main__':
    app.run(debug=False, port=80, host='0.0.0.0')