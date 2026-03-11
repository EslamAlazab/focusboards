from rest_framework import serializers
from apis.boards.models import Board
from .models import BoardAIChat, BoardAIMessage, BoardMemory, AIProviderSettings


class BoardAIChatSerializer(serializers.ModelSerializer):

    class Meta:
        model = BoardAIChat
        fields = ['id', 'board', 'title', 'created_at']
        read_only_fields = ['board']


class BoardAIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardAIMessage
        fields = ['id', 'chat', 'role', 'content', 'created_at']
        read_only_fields = ['created_at', 'chat', 'role']


class BoardMemorySerializer(serializers.ModelSerializer):

    class Meta:
        model = BoardMemory
        fields = ['id', 'board', 'content', 'memory_type', 'is_pinned', 'created_at']
        read_only_fields = ['created_at', 'board', 'memory_type', 'is_pinned']


class AIProviderSettingsRetrieveSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = AIProviderSettings
        fields = ['id', 'user', 'model_name', 'base_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class AIProviderSettingsUpdateSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True)
    class Meta:
        model = AIProviderSettings
        fields = ['model_name', 'api_key', 'base_url']
