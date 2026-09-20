from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TimelineEventViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'events', TimelineEventViewSet, basename='timeline-events')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
]
