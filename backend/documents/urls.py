from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, DocumentVersionViewSet, DocumentCommentViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='documents')
router.register(r'versions', DocumentVersionViewSet, basename='document-versions')
router.register(r'comments', DocumentCommentViewSet, basename='document-comments')

urlpatterns = [
    path('', include(router.urls)),
]
