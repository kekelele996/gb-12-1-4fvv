from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApplicationProjectViewSet

router = DefaultRouter()
router.register(r'projects', ApplicationProjectViewSet, basename='application-projects')

urlpatterns = [
    path('', include(router.urls)),
]
