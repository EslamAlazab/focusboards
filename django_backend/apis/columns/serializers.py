from rest_framework import serializers
from .models import Column

class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model= Column
        fields = ['id', 'title', 'order', 'color', 'created_at', 'updated_at', 'board']
        read_only_fields = ['board', 'created_at', 'updated_at']


class ColumnUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ['title', 'order', 'color', 'board']

    def validate_board(self, new_board):
        request = self.context['request']
        user = request.user

        if new_board and new_board.owner != user:
            raise serializers.ValidationError(
                "You can only create or move columns to your own boards."
            )

        return new_board