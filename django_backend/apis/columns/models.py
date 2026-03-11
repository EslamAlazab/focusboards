from uuid import uuid4
from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator

from apis.boards.models import Board
from apis.users.models import User

class Column(models.Model):
    id = models.UUIDField(default=uuid4,primary_key=True, editable=False)
    title = models.CharField(max_length=150, null=False, validators=[MinLengthValidator(3)])
    color = models.CharField(
        max_length=7,
        default="#ffffff",
        validators=[
            RegexValidator(regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', message='Color must be in hex format', code='invalid_hex_color')
        ]
    )
    order = models.PositiveSmallIntegerField()
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name= "columns")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name= "columns")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
