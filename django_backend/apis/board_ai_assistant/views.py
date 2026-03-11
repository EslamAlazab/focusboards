from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics, mixins, viewsets
from rest_framework.decorators import action 
from rest_framework.response import Response
from django.http import StreamingHttpResponse

from .models import BoardAIChat, BoardAIMessage, BoardMemory, AIProviderSettings
from .serializers import (
    BoardAIChatSerializer,
    BoardAIMessageSerializer,
    BoardMemorySerializer,
    AIProviderSettingsRetrieveSerializer,
    AIProviderSettingsUpdateSerializer,
)
from .services.ai_chat_service import BoardAIChatService
from .schemas import (
    board_ai_chats_schema, board_ai_chat_detail_schema, board_ai_chat_messages_schema,
    ai_chat_message_detail_schema, board_memories_schema, memory_detail_schema, ai_provider_settings_schema,
)


@board_ai_chats_schema
class BoardAIChatsView(generics.ListCreateAPIView):
    serializer_class = BoardAIChatSerializer
    permission_classes = [permissions.IsAuthenticated,]

    def get_queryset(self):
        board_id = self.kwargs.get('board_id')
        return BoardAIChat.objects.filter(board__owner=self.request.user, board_id=board_id)

    def perform_create(self, serializer):
        board_id = self.kwargs.get('board_id')
        serializer.save(board_id=board_id)


@board_ai_chat_detail_schema
class BoardAIchatDetailViewSet(viewsets.GenericViewSet,
                mixins.RetrieveModelMixin,  
                mixins.UpdateModelMixin, 
                mixins.DestroyModelMixin):
    serializer_class = BoardAIChatSerializer
    permission_classes = [permissions.IsAuthenticated,]

    def get_queryset(self):
        return BoardAIChat.objects.filter(board__owner=self.request.user)


@board_ai_chat_messages_schema
class BoardAIChatMessagesView(generics.ListCreateAPIView):
    serializer_class = BoardAIMessageSerializer
    permission_classes = [permissions.IsAuthenticated,]

    def get_queryset(self):
        return BoardAIMessage.objects.filter(
            chat_id=self.kwargs["chat_id"],
            chat__board__owner=self.request.user,
        ).select_related('chat__board')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        chat = get_object_or_404(
            BoardAIChat,
            pk=self.kwargs["chat_id"],
            board__owner=request.user,
        )

        user_message = serializer.validated_data["content"]

        BoardAIMessage.objects.create(
            chat=chat,
            role="user",
            content=user_message,
        )

        llm_settings = get_object_or_404(AIProviderSettings,user=request.user)

        service = BoardAIChatService(chat, llm_settings)

        response = StreamingHttpResponse(
            service.stream_chat_response(user_message),
            content_type="text/event-stream",
        )

        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # for nginx

        return response


@ai_chat_message_detail_schema
class AIChatMessageDetailView(viewsets.GenericViewSet,
                mixins.RetrieveModelMixin,  
                mixins.UpdateModelMixin, 
                mixins.DestroyModelMixin):
    
    serializer_class = BoardAIMessageSerializer
    permission_classes = [permissions.IsAuthenticated,]

    def get_queryset(self):
        return BoardAIMessage.objects.filter(
            chat__board__owner=self.request.user,
        )


@board_memories_schema
class BoardMemoriesView(generics.ListCreateAPIView):
    
    serializer_class = BoardMemorySerializer
    permission_classes = [permissions.IsAuthenticated,]

    def get_queryset(self):
        board_id = self.kwargs.get("board_id")
        return BoardMemory.objects.filter(
            board__owner=self.request.user,
            board_id=board_id,
)
    
    def perform_create(self, serializer):
        board_id = self.kwargs.get('board_id')
        serializer.save(board_id=board_id, memory_type = 'manual', is_pinned=True)


@memory_detail_schema
class MemoryDetailViewSet(viewsets.GenericViewSet,
                mixins.RetrieveModelMixin,
                mixins.UpdateModelMixin,
                mixins.DestroyModelMixin):
    
    serializer_class = BoardMemorySerializer
    permission_classes = [permissions.IsAuthenticated,]

    def get_queryset(self):
        return BoardMemory.objects.filter(board__owner=self.request.user)
    
    @action(methods=['POST'], detail=True, url_path='toggle_is_pinned')
    def is_pinned_toggle(self, request, pk=None):
        memory = self.get_object()
        memory.is_pinned = not memory.is_pinned
        memory.save()
        serializer = self.get_serializer(memory)
        return Response(serializer.data)


@ai_provider_settings_schema
class AIProviderSettingsView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AIProviderSettings.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return AIProviderSettingsUpdateSerializer
        return AIProviderSettingsRetrieveSerializer

    def get_object(self):
        obj, _ = AIProviderSettings.objects.get_or_create(user=self.request.user)
        return obj
