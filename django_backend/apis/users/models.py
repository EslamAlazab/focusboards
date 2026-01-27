from django.db import models
from django.contrib.auth.models import AbstractUser
from uuid import uuid4

class User(AbstractUser):
    id = models.UUIDField(default=uuid4,primary_key=True, editable=False)
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    google_id = models.CharField(max_length=255, blank=True, null=True)
    is_guest = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


