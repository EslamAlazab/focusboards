from uuid import uuid4
from django.db import models
from django.core.validators import MinLengthValidator

from apis.users.models import User

class Project(models.Model):
    id = models.UUIDField(default=uuid4,primary_key=True, editable=False)
    name = models.CharField(max_length=150, null=False, db_index=True, validators=[MinLengthValidator(3)])
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects",)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"