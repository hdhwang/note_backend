import base64
import logging

from Crypto.Cipher import AES
from django.conf import settings

from utils.format_helper import to_str

logger = logging.getLogger(__name__)

BLOCK_SIZE = 32
pad = (
    lambda s: s
    + (BLOCK_SIZE - len(s) % BLOCK_SIZE)
    * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE).encode()
)
unpad = lambda s: s[: -ord(s[len(s) - 1 :])]


class AESCipher(object):
    def __init__(self, key, iv):
        self.key = bytes.fromhex(key)
        self.iv = bytes.fromhex(iv)

    def encrypt(self, message):
        try:
            message = message.encode()
            raw = pad(message)
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            enc = cipher.encrypt(raw)
            return base64.b64encode(enc).decode("utf-8")

        except Exception as e:
            logger.warning(f"[encrypt] {to_str(e)}")

    def decrypt(self, enc):
        try:
            enc = base64.b64decode(enc)
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            dec = cipher.decrypt(enc)
            return unpad(dec).decode("utf-8")

        except Exception as e:
            logger.warning(f"[decrypt] {to_str(e)}")


# 키 값 암호화 수행
def make_enc_value(value):
    result = value

    try:
        key = getattr(settings, "AES_KEY")
        iv = getattr(settings, "AES_KEY_IV")
        aes = AESCipher(key, iv)

        result = aes.encrypt(value)

    except Exception as e:
        logger.warning(f"[NoteAPI - make_enc_value] {to_str(e)}")

    finally:
        return result


# 키 값 복호화 수행
def get_dec_value(enc_value):
    result = enc_value

    try:
        key = getattr(settings, "AES_KEY")
        iv = getattr(settings, "AES_KEY_IV")
        aes = AESCipher(key, iv)

        result = aes.decrypt(enc_value)

    except Exception as e:
        logger.warning(f"[NoteAPI - get_dec_value] {to_str(e)}")

    finally:
        return result
