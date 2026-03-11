import base64
import hashlib
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet

class EncryptedTextField(models.TextField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Derive a valid 32-byte base64 Fernet key from the Django SECRET_KEY
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key)
        self.cipher = Fernet(fernet_key)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        return self.cipher.encrypt(str(value).encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self.cipher.decrypt(value.encode()).decode()

    def to_python(self, value):
        if value is None:
            return value
        try:
            return self.cipher.decrypt(value.encode()).decode()
        except Exception:
            return value