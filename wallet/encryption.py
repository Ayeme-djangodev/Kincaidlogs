import base64
import json
import xml.etree.ElementTree as ET

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from django.conf import settings


class RSAEncryptionError(Exception):
    pass


class RSAEncryptor:
    def __init__(self):
        key = settings.TRANSACTPAY_ENCRYPTION_KEY

        if not key:
            raise RSAEncryptionError(
                "TRANSACTPAY_ENCRYPTION_KEY is missing."
            )

        self.public_key = self._load_xml_key(key)
        self.cipher = PKCS1_v1_5.new(self.public_key)

    def _load_xml_key(self, encoded_key: str):
        """
        Converts TransactPay's Base64-encoded XML RSA key into a PyCryptodome RSA key.
        """

        try:
            xml = base64.b64decode(encoded_key).decode("utf-8")

            # remove the leading "4096!"
            if "!" in xml:
                xml = xml.split("!", 1)[1]

            root = ET.fromstring(xml)

            modulus = root.findtext("Modulus")
            exponent = root.findtext("Exponent")

            if not modulus or not exponent:
                raise RSAEncryptionError(
                    "Invalid RSA XML key."
                )

            n = int.from_bytes(base64.b64decode(modulus), "big")
            e = int.from_bytes(base64.b64decode(exponent), "big")

            return RSA.construct((n, e))

        except Exception as exc:
            raise RSAEncryptionError(
                "Unable to parse TransactPay RSA key."
            ) from exc

    def encrypt(self, payload: dict) -> str:
        plaintext = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        encrypted = self.cipher.encrypt(plaintext)

        return base64.b64encode(encrypted).decode("utf-8")