from uuid import uuid4
from django.db import models
from django.core.validators import MinLengthValidator

from apis.users.models import User
from apis.boards.models import Board
from apis.columns.models import Column

class Task(models.Model):
    id = models.UUIDField(default=uuid4,primary_key=True, editable=False)
    title = models.CharField(max_length=150, null=False, validators=[MinLengthValidator(3)])
    content = models.TextField(blank=True, default='')
    order = models.PositiveSmallIntegerField()
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name= "tasks")
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name= "tasks", null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name= "tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order','created_at']
