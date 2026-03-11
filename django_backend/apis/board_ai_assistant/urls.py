from django.urls import path
from rest_framework import routers

from .views import (
    BoardAIChatsView,
    BoardAIchatDetailViewSet,
    BoardAIChatMessagesView,
    BoardMemoriesView,
    AIChatMessageDetailView,
    MemoryDetailViewSet,
    AIProviderSettingsView,
)

router = routers.DefaultRouter()
router.register(r'chats', BoardAIchatDetailViewSet, basename='ai-chat')
router.register(r'chat-messages', AIChatMessageDetailView, basename='ai-chat-message')
router.register(r'memories', MemoryDetailViewSet, basename='ai-memory')

urlpatterns = [
    path('chats/<uuid:board_id>/', BoardAIChatsView.as_view(), name='board-ai-chats'),
    path('chat/<int:chat_id>/',BoardAIChatMessagesView.as_view(), name='chat-messages' ),
    path('memories/<uuid:board_id>/',BoardMemoriesView.as_view(), name='board-ai-memories' ),
    path('settings/', AIProviderSettingsView.as_view(), name='ai-provider-settings'),
] + router.urls