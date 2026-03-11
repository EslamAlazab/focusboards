from sentence_transformers import SentenceTransformer

_model = None
MODEL_NAME = "all-MiniLM-L6-v2"

def get_model():
    """
    Returns the singleton instance of the sentence transformer model.
    Loads the model on first call.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def load_model():
    """
    Explicitly loads the model into memory.
    This can be called at application startup to pre-warm the model.
    """
    get_model()


def embed_text(text: str) -> list[float]:
    model = get_model()
    return model.encode(text, normalize_embeddings=True).tolist()