from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    University, Program, ApplicationRequirement, 
    ApplicationDeadline, UniversityRecommendation
)
from .serializers import (
    UniversitySerializer, UniversityDetailSerializer,
    ProgramSerializer, ProgramListSerializer,
    ApplicationRequirementSerializer, ApplicationDeadlineSerializer,
    UniversityRecommendationSerializer
)
from .filters import UniversityFilter, ProgramFilter

class UniversityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UniversityFilter
    search_fields = ['name', 'country', 'city']
    ordering_fields = ['qs_ranking', 'times_ranking', 'name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UniversityDetailSerializer
        return UniversitySerializer

class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProgramFilter
    search_fields = ['name', 'department']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProgramListSerializer
        return ProgramSerializer

class UniversityRecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = UniversityRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'consultant':
            return UniversityRecommendation.objects.filter(consultant=user)
        elif user.role == 'student':
            return UniversityRecommendation.objects.filter(student=user)
        return UniversityRecommendation.objects.all()
    
    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        recommendation = self.get_object()
        recommendation.is_viewed = True
        recommendation.save()
        return Response({'status': 'marked as viewed'})
