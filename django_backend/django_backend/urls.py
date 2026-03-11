from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
     # API Schema:
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    path('admin/', admin.site.urls),
    path('api/v1/', include("apis.users.urls")),
    path('api/v1/user-projects/', include("apis.projects.urls")),
    path('api/v1/boards/', include("apis.boards.urls")),
    path('api/v1/columns/', include("apis.columns.urls")),
    path('api/v1/tasks/', include("apis.tasks.urls")),
    path('api/v1/board-ai/', include("apis.board_ai_assistant.urls")),
]
