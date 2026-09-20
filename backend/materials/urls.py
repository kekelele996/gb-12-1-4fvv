from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaterialItemViewSet, MaterialTemplateViewSet

router = DefaultRouter()
router.register(r'items', MaterialItemViewSet, basename='materials')
router.register(r'templates', MaterialTemplateViewSet, basename='material-templates')

urlpatterns = [
    path('', include(router.urls)),
]
