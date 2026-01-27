from django.urls import path
from rest_framework import routers
from .views import BoardColumnsView, ColumnView

router = routers.DefaultRouter()
router.register('', ColumnView, basename='columns')

urlpatterns = [
    path('board-columns/<uuid:board_id>/', BoardColumnsView.as_view(), name='board_column'),
] + router.urls