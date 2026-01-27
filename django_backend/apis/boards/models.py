from uuid import uuid4
from django.db import models
from django.core.validators import MinLengthValidator

from apis.users.models import User
from apis.projects.models import Project

class Board(models.Model):
    id = models.UUIDField(default=uuid4,primary_key=True, editable=False)
    title = models.CharField(max_length=150, null=False, validators=[MinLengthValidator(3)])
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="boards")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="boards")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
