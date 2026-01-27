from rest_framework import routers
from .views import UserProjectsView

router = routers.DefaultRouter()
router.register('', UserProjectsView, basename='user-projects')

urlpatterns = router.urls