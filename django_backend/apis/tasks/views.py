from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.viewsets import GenericViewSet
from rest_framework import permissions, mixins

from .models import Task, Column, Board
from .serializers import TaskSerializer

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


@extend_schema(tags=['tasks'])
@extend_schema_view(
    get=extend_schema(summary='List the column tasks')
)
class ColumnTasksView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        column_id = self.kwargs.get('column_id')
        return Task.objects.filter(owner=user, column_id=column_id)
    
    def perform_create(self, serializer):
        column = get_object_or_404(
            Column,
            id=self.kwargs['column_id'],
            owner=self.request.user
        )
        serializer.save(owner=self.request.user, board=column.board , column=column)


@extend_schema(
    tags=['tasks'],
    summary="get the unassigned tasks for a board"
    )
class BoardUnassignedTasks(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        board_id = self.kwargs.get('board_id')
        return Task.objects.filter(owner=user, board_id=board_id, column_id=None)
    
    def perform_create(self, serializer):
        user = self.request.user
        board = get_object_or_404(
            Board,
            id = self.kwargs['board_id'],
            owner=user
        )
        serializer.save(owner=user, board=board, column_id=None)


@extend_schema(
    tags=['tasks'],
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
        )
    ]
)
class TasksView(GenericViewSet, 
                mixins.RetrieveModelMixin, 
                mixins.UpdateModelMixin, 
                mixins.DestroyModelMixin):
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)