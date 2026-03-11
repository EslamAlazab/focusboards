from django.db import models
from pgvector.django import VectorField, HnswIndex
from .services.encryption_field import EncryptedTextField

from apis.users.models import User
from apis.boards.models import Board
from .services.embeddings import embed_text


class BoardAIChat(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="ai_chats")
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class BoardAIMessage(models.Model):
    chat = models.ForeignKey(BoardAIChat, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(choices=[
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["chat", "created_at"])
        ]


class BoardMemory(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="ai_memories")
    content = models.TextField()
    memory_type = models.CharField(choices=[
        ("manual", "Manual"),
        ("auto", "Auto"),
    ])
    is_pinned = models.BooleanField(default=False)
    embedding = VectorField(dimensions=384, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["board", "is_pinned", "memory_type"]),
            HnswIndex(
                name="memory_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]

    def save(self, *args, **kwargs):
        # Re-calculate embedding if content is present and (embedding is missing OR content changed)
        if self.content:
            should_embed = self.embedding is None
            
            if not should_embed and self.pk:
                original = BoardMemory.objects.get(pk=self.pk)
                if original.content != self.content:
                    should_embed = True
            
            if should_embed:
                self.embedding = embed_text(self.content)
        
        super().save(*args, **kwargs)


class AIProviderSettings(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="ai_settings",
    )
    model_name = models.CharField(max_length=255)
    api_key = EncryptedTextField()
    base_url = models.URLField(default="https://openrouter.ai/api/v1")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)