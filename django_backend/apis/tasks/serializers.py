from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'content', 'order', 'column', 'created_at', 'updated_at']
        read_only_fields = ['column', 'created_at', 'updated_at']


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['title', 'content', 'order', 'column']

    def validate_column(self, new_column):
        request = self.context['request']
        user = request.user

        if new_column and new_column.owner != user:
            raise serializers.ValidationError(
                "You can only create or move tasks to your own boards."
            )

        return new_column
    
    