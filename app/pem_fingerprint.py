import base64
import hashlib
from pathlib import Path

from OpenSSL import crypto

from config.config import Config


class PEMFingerprint():

    @property
    def fingerprint(self) -> str | None:
        if Config.GITHUB_BOT_PRIVATE_KEY_PATH == '':
            return None

        path = Path(Config.GITHUB_BOT_PRIVATE_KEY_PATH)
        if not path.exists():
            return None

        with open(path, 'rb') as f:
            private_key = crypto.load_privatekey(crypto.FILETYPE_PEM, f.read())

        public_key = crypto.dump_publickey(crypto.FILETYPE_ASN1, private_key)
        sha256_hash = hashlib.sha256(public_key).digest()
        base64_encoded = base64.b64encode(sha256_hash)
        return self.hide_text(base64_encoded.decode())

    def hide_text(self, origin: str, replace_char: str = '*') -> str:
        hide_length = int(len(origin) / 2)
        median = int(len(origin) / 2)
        hide_string = origin[median - int(hide_length / 2) - 1:median + int(hide_length / 2) + 1]
        return origin.replace(hide_string, replace_char * len(hide_string))
