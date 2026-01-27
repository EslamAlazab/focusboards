from rest_framework import serializers
from .models import Column

class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model= Column
        exclude = ['owner']
        extra_kwargs = {
            'board': {'required': False}
        }

    def validate_board(self, new_board):
        request = self.context['request']
        user = request.user

        if new_board.owner != user:
            raise serializers.ValidationError(
                "You can only create or move columns to your own boards."
            )

        return new_board