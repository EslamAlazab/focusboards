from django.apps import AppConfig


class BoardAiAssistantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apis.board_ai_assistant'

    def ready(self):
        """
        This method is called once Django is ready. We use it to pre-load
        the sentence-transformer model into memory for each worker process.
        This avoids a long delay on the first API call that requires embeddings,
        which is crucial for a good user experience and to prevent request timeouts.
        """
        from .services import embeddings
        embeddings.load_model()
