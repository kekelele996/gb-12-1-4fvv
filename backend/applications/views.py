from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import ApplicationProject, StatusChangeHistory
from .serializers import (
    ApplicationProjectSerializer, ApplicationProjectListSerializer,
    StatusChangeHistorySerializer
)

class ApplicationProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return ApplicationProject.objects.filter(student=user)
        elif user.role == 'consultant':
            students = [sp.user for sp in user.students.all()]
            return ApplicationProject.objects.filter(student__in=students)
        return ApplicationProject.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicationProjectListSerializer
        return ApplicationProjectSerializer
    
    @transaction.atomic
    def perform_update(self, serializer):
        instance = self.get_object()
        old_status = instance.status
        new_status = serializer.validated_data.get('status', old_status)
        
        if old_status != new_status:
            StatusChangeHistory.objects.create(
                application=instance,
                from_status=old_status,
                to_status=new_status,
                changed_by=self.request.user
            )
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        application = self.get_object()
        old_status = application.status
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')
        
        if new_status not in [choice[0] for choice in ApplicationProject.STATUS_CHOICES]:
            return Response({'error': '无效的状态值'}, status=status.HTTP_400_BAD_REQUEST)
        
        application.status = new_status
        application.save()
        
        StatusChangeHistory.objects.create(
            application=application,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            change_reason=reason
        )
        
        return Response(ApplicationProjectSerializer(application).data)
    
    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        application = self.get_object()
        history = application.status_history.all()
        serializer = StatusChangeHistorySerializer(history, many=True)
        return Response(serializer.data)
