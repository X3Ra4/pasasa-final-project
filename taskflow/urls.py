from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from board.api import ProjectViewSet, TaskViewSet

router = DefaultRouter()
router.register('projects', ProjectViewSet, basename='api-project')
router.register('tasks', TaskViewSet, basename='api-task')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('board.urls')),
]
admin.site.site_header = 'TaskFlow · Адміністрування'
admin.site.site_title = 'TaskFlow'
