import hashlib
import hmac

from flask import Request
from loguru import logger


class ValidateSignature():
    def preprocessing(self, request: Request, signature: str) -> tuple[str, str, bytes]:
        match signature:
            case 'sha1':
                signature_header_name = 'X-Hub-Signature'
            case 'sha256':
                signature_header_name = 'X-Hub-Signature-256'
            case _:
                raise ValueError(f'Unsupported signature algorithm: {signature}')
        signature_header = request.headers[signature_header_name]
        sha_name, github_signature = signature_header.split('=')
        body = request.get_data()
        return (sha_name, github_signature, body)

    def _verify(self, request: Request, secret: str, algorithm: str) -> bool:
        """共用的簽名驗證邏輯。"""
        sha_name, github_signature, body = self.preprocessing(request, algorithm)
        if sha_name != algorithm:
            logger.error(f'ERROR: Signature header hash name was not {algorithm}')
            return False

        digestmod = hashlib.sha256 if algorithm == 'sha256' else hashlib.sha1
        local_signature = hmac.HMAC(
            secret.encode('utf-8'), msg=body, digestmod=digestmod
        )
        return hmac.compare_digest(local_signature.hexdigest(), github_signature)

    def sha1(self, request: Request, secret: str) -> bool:
        return self._verify(request, secret, 'sha1')

    def sha256(self, request: Request, secret: str) -> bool:
        return self._verify(request, secret, 'sha256')
