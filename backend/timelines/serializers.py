from rest_framework import serializers
from .models import TimelineEvent, Notification

class TimelineEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = TimelineEvent
        fields = ['id', 'application', 'event_type', 'event_type_display',
                  'title', 'description', 'event_date', 'deadline_date',
                  'reminder_sent', 'is_completed', 'completed_at',
                  'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'reminder_sent', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'notification_type', 'notification_type_display',
                  'priority', 'priority_display', 'title', 'content',
                  'related_event', 'related_application', 'is_read',
                  'read_at', 'sent_at', 'created_at']
        read_only_fields = ['id', 'recipient', 'sent_at', 'created_at']
