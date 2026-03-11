from pgvector.django import CosineDistance
from apis.board_ai_assistant.models import BoardMemory
from .embeddings import embed_text


def search_similar_memories(board, query, top_k=5):
    query_embedding = embed_text(query)

    return (
        BoardMemory.objects
        .filter(board=board, is_pinned=False)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:top_k]
    )


def get_pinned_memories(board):
    return (
        BoardMemory.objects
        .filter(board=board, is_pinned=True)[:10]
    )
