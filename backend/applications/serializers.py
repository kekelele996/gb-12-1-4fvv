from rest_framework import serializers
from .models import ApplicationProject, StatusChangeHistory
from universities.serializers import UniversitySerializer, ProgramSerializer
from users.serializers import UserSerializer

class StatusChangeHistorySerializer(serializers.ModelSerializer):
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = StatusChangeHistory
        fields = ['id', 'application', 'from_status', 'from_status_display',
                  'to_status', 'to_status_display', 'changed_by', 
                  'changed_by_name', 'change_reason', 'created_at']
        read_only_fields = ['id', 'application', 'changed_by', 'created_at']

class ApplicationProjectSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    student_name = serializers.CharField(source='student.username', read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    materials_progress = serializers.SerializerMethodField()
    status_history = StatusChangeHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = ApplicationProject
        fields = ['id', 'student', 'student_name', 'university', 'university_name',
                  'program', 'program_name', 'application_round', 'status', 
                  'status_display', 'notes', 'application_fee', 'fee_paid',
                  'submitted_at', 'result_date', 'materials_progress',
                  'status_history', 'created_at', 'updated_at']
        read_only_fields = ['id', 'student', 'status_history', 'created_at', 'updated_at']
    
    def get_materials_progress(self, obj):
        return obj.get_materials_progress()
    
    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)

class ApplicationProjectListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    materials_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = ApplicationProject
        fields = ['id', 'university', 'university_name', 'program', 'program_name',
                  'status', 'status_display', 'materials_progress',
                  'submitted_at', 'created_at']
    
    def get_materials_progress(self, obj):
        return obj.get_materials_progress()
