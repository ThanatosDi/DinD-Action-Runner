import hashlib
import hmac

import pytest
from werkzeug.test import EnvironBuilder

from app.validate_signature import ValidateSignature


def _make_request(body: bytes, signature_header: str, header_name: str = "X-Hub-Signature-256"):
    """建立一個帶有簽名標頭的模擬 Flask Request。"""
    builder = EnvironBuilder(method="POST", data=body, headers={header_name: signature_header})
    env = builder.get_environ()
    from flask import Flask
    app = Flask(__name__)
    with app.request_context(env):
        from flask import request
        yield request


def _sign(body: bytes, secret: str, algorithm: str = "sha256") -> str:
    """使用指定演算法產生 HMAC 簽名。"""
    digestmod = hashlib.sha256 if algorithm == "sha256" else hashlib.sha1
    sig = hmac.new(secret.encode("utf-8"), msg=body, digestmod=digestmod).hexdigest()
    return f"{algorithm}={sig}"


@pytest.fixture()
def validator():
    return ValidateSignature()


class TestValidateSignatureSHA1:
    """SHA1 簽名驗證測試"""

    def test_valid_sha1_signature(self, validator):
        """3.1.1 有效的 SHA1 簽名回傳 True"""
        body = b'{"action": "queued"}'
        secret = "test-secret"
        sig = _sign(body, secret, "sha1")
        for req in _make_request(body, sig, "X-Hub-Signature"):
            assert validator.sha1(req, secret) is True

    def test_invalid_sha1_signature(self, validator):
        """3.1.2 無效的 SHA1 簽名回傳 False"""
        body = b'{"action": "queued"}'
        secret = "test-secret"
        sig = "sha1=0000000000000000000000000000000000000000"
        for req in _make_request(body, sig, "X-Hub-Signature"):
            assert validator.sha1(req, secret) is False

    def test_sha1_wrong_algorithm_name(self, validator):
        """3.1.3 SHA1 標頭格式錯誤（hash 名稱不是 sha1）回傳 False"""
        body = b'{"action": "queued"}'
        secret = "test-secret"
        sig = "md5=abcdef1234567890"
        for req in _make_request(body, sig, "X-Hub-Signature"):
            assert validator.sha1(req, secret) is False


class TestValidateSignatureSHA256:
    """SHA256 簽名驗證測試"""

    def test_valid_sha256_signature(self, validator):
        """3.1.4 有效的 SHA256 簽名回傳 True"""
        body = b'{"action": "queued"}'
        secret = "test-secret"
        sig = _sign(body, secret, "sha256")
        for req in _make_request(body, sig, "X-Hub-Signature-256"):
            assert validator.sha256(req, secret) is True

    def test_invalid_sha256_signature(self, validator):
        """3.1.5 無效的 SHA256 簽名回傳 False"""
        body = b'{"action": "queued"}'
        secret = "test-secret"
        sig = "sha256=" + "0" * 64
        for req in _make_request(body, sig, "X-Hub-Signature-256"):
            assert validator.sha256(req, secret) is False

    def test_sha256_wrong_algorithm_name(self, validator):
        """3.1.6 SHA256 標頭格式錯誤（hash 名稱不是 sha256）回傳 False"""
        body = b'{"action": "queued"}'
        secret = "test-secret"
        sig = "md5=abcdef1234567890"
        for req in _make_request(body, sig, "X-Hub-Signature-256"):
            assert validator.sha256(req, secret) is False


class TestPreprocessing:
    """preprocessing 方法測試"""

    def test_parse_signature_header(self, validator):
        """3.1.7 正確解析 algorithm=signature 格式"""
        body = b'{"test": true}'
        sig = "sha256=abc123def456"
        for req in _make_request(body, sig, "X-Hub-Signature-256"):
            sha_name, github_sig, req_body = validator.preprocessing(req, "sha256")
            assert sha_name == "sha256"
            assert github_sig == "abc123def456"
            assert req_body == body
