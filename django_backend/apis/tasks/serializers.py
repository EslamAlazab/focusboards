from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model= Task
        exclude = ['owner', "board"]  

    def validate_column(self, new_column):
        request = self.context['request']
        user = request.user

        if new_column.owner != user:
            raise serializers.ValidationError(
                "You can only create or move tasks to your own boards."
            )

        return new_column
    
    