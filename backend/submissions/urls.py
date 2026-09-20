from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SubmissionSnapshotViewSet

router = DefaultRouter()
router.register(r'snapshots', SubmissionSnapshotViewSet, basename='submission-snapshots')

urlpatterns = [
    path('', include(router.urls)),
]
