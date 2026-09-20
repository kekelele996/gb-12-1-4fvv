from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import TimelineEvent, Notification
from .serializers import TimelineEventSerializer, NotificationSerializer

class TimelineEventViewSet(viewsets.ModelViewSet):
    serializer_class = TimelineEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        application_id = self.request.query_params.get('application_id')
        if application_id:
            return TimelineEvent.objects.filter(application_id=application_id)
        
        user = self.request.user
        if user.role == 'student':
            return TimelineEvent.objects.filter(application__student=user)
        elif user.role == 'consultant':
            students = [sp.user for sp in user.students.all()]
            return TimelineEvent.objects.filter(application__student__in=students)
        return TimelineEvent.objects.all()
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        event = self.get_object()
        event.is_completed = True
        event.completed_at = timezone.now()
        event.save()
        return Response(TimelineEventSerializer(event).data)
    
    @action(detail=True, methods=['post'])
    def mark_incomplete(self, request, pk=None):
        event = self.get_object()
        event.is_completed = False
        event.completed_at = None
        event.save()
        return Response(TimelineEventSerializer(event).data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        user = self.request.user
        days_ahead = int(request.query_params.get('days', 7))
        
        if user.role == 'student':
            events = TimelineEvent.objects.filter(
                application__student=user,
                is_completed=False,
                event_date__range=[timezone.now(), timezone.now() + timezone.timedelta(days=days_ahead)]
            )
        elif user.role == 'consultant':
            students = [sp.user for sp in user.students.all()]
            events = TimelineEvent.objects.filter(
                application__student__in=students,
                is_completed=False,
                event_date__range=[timezone.now(), timezone.now() + timezone.timedelta(days=days_ahead)]
            )
        else:
            events = TimelineEvent.objects.filter(
                is_completed=False,
                event_date__range=[timezone.now(), timezone.now() + timezone.timedelta(days=days_ahead)]
            )
        
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response(NotificationSerializer(notification).data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        notifications = self.get_queryset().filter(is_read=False)
        notifications.update(is_read=True, read_at=timezone.now())
        return Response({'status': 'all marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
