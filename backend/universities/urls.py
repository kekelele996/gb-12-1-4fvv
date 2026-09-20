from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UniversityViewSet, ProgramViewSet, UniversityRecommendationViewSet

router = DefaultRouter()
router.register(r'universities', UniversityViewSet)
router.register(r'programs', ProgramViewSet)
router.register(r'recommendations', UniversityRecommendationViewSet, basename='university-recommendations')

urlpatterns = [
    path('', include(router.urls)),
]
