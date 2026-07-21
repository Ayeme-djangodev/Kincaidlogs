from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _get_fernet():
    return Fernet(settings.FIELD_ENCRYPTION_KEY.encode())


class EncryptedTextField(models.TextField):
    """
    A TextField that is transparently encrypted at rest using Fernet
    (symmetric, authenticated encryption). Reads/writes plain strings
    in Python; the database only ever sees ciphertext.
    """

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        return _get_fernet().encrypt(str(value).encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        try:
            return _get_fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            # Value predates encryption being enabled, or key changed.
            # Fail safe by returning it as-is rather than crashing the page.
            return value
