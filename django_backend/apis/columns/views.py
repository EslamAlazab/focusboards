from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.viewsets import GenericViewSet
from rest_framework import permissions, mixins

from .models import Column, Board
from .serializers import ColumnSerializer, ColumnUpdateSerializer

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


@extend_schema(tags=['columns'])
@extend_schema_view(
    get=extend_schema(summary='List the board columns')
)
class BoardColumnsView(generics.ListCreateAPIView):
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        board_id = self.kwargs.get('board_id')
        return Column.objects.filter(owner=user, board_id=board_id)
    
    def perform_create(self, serializer):
        board = get_object_or_404(
            Board,
            id=self.kwargs['board_id'],
            owner=self.request.user
        )
        serializer.save(board=board, owner=self.request.user)
    

@extend_schema(
    tags=['columns'],
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
        )
    ]
)
class ColumnView(GenericViewSet, 
                mixins.RetrieveModelMixin, 
                mixins.UpdateModelMixin, 
                mixins.DestroyModelMixin):
    
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Column.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ColumnUpdateSerializer
        return ColumnSerializer