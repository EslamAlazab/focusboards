from django.urls import path
from rest_framework import routers
from .views import ProjectBoardsView, BoardView

router = routers.DefaultRouter()
router.register('', BoardView, basename='boards')

urlpatterns = [
    path('project-boards/<uuid:project_id>/', ProjectBoardsView.as_view(), name='project-boards'),
] + router.urls