from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions, filters

from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from drf_spectacular.types import OpenApiTypes

from .models import Project
from .serializers import ProjectSerializer


@extend_schema(
    tags=['projects'],
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
        )
    ]
)
@extend_schema_view(
    list=extend_schema(summary='List the user project')
)
class UserProjectsView(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(owner=user).order_by('created_at')
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
