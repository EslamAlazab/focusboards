from django.urls import path
from rest_framework import routers
from .views import ColumnTasksView, BoardUnassignedTasks, TasksView

router = routers.DefaultRouter()
router.register('', TasksView, basename='tasks')

urlpatterns = [
    path('column-tasks/<uuid:column_id>/', ColumnTasksView.as_view(), name='column_tasks'),
    path('unassigned-tasks/<uuid:board_id>', BoardUnassignedTasks.as_view(), name='unassigned_tasks'),
] + router.urls