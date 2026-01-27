from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.viewsets import GenericViewSet
from rest_framework import permissions, mixins

from .models import Board, Project
from .serializers import BoardSerializer

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


@extend_schema(tags=['boards'])
@extend_schema_view(
    get=extend_schema(summary='List the project boards')
)
class ProjectBoardsView(generics.ListCreateAPIView):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        project_id = self.kwargs.get('project_id')
        return Board.objects.filter(owner=user, project_id=project_id).order_by('created_at')
    
    def perform_create(self, serializer):
        project = get_object_or_404(
            Project,
            id=self.kwargs['project_id'],
            owner=self.request.user
        )
        serializer.save(owner=self.request.user, project=project)
    

@extend_schema(
    tags=['boards'],
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
        )
    ]
)
class BoardView(GenericViewSet, 
                mixins.RetrieveModelMixin, 
                mixins.UpdateModelMixin, 
                mixins.DestroyModelMixin):
    
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Board.objects.filter(owner=self.request.user)