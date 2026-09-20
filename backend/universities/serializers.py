from rest_framework import serializers
from .models import (
    University, Program, ApplicationRequirement, 
    ApplicationDeadline, UniversityRecommendation
)

class ApplicationRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationRequirement
        fields = '__all__'

class ApplicationDeadlineSerializer(serializers.ModelSerializer):
    round_name_display = serializers.CharField(source='get_round_name_display', read_only=True)
    
    class Meta:
        model = ApplicationDeadline
        fields = '__all__'

class ProgramSerializer(serializers.ModelSerializer):
    degree_level_display = serializers.CharField(source='get_degree_level_display', read_only=True)
    requirements = ApplicationRequirementSerializer(read_only=True)
    deadlines = ApplicationDeadlineSerializer(many=True, read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)
    
    class Meta:
        model = Program
        fields = ['id', 'university', 'university_name', 'name', 'degree_level', 
                  'degree_level_display', 'department', 'description', 
                  'duration_years', 'tuition', 'language_of_instruction',
                  'requirements', 'deadlines', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ProgramListSerializer(serializers.ModelSerializer):
    degree_level_display = serializers.CharField(source='get_degree_level_display', read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)
    
    class Meta:
        model = Program
        fields = ['id', 'name', 'university', 'university_name', 
                  'degree_level', 'degree_level_display', 
                  'department', 'tuition']

class UniversitySerializer(serializers.ModelSerializer):
    programs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = University
        fields = ['id', 'name', 'country', 'city', 'qs_ranking', 
                  'times_ranking', 'description', 'logo', 'website',
                  'tuition_min', 'tuition_max', 'tuition_currency',
                  'programs_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_programs_count(self, obj):
        return obj.programs.count()

class UniversityDetailSerializer(serializers.ModelSerializer):
    programs = ProgramListSerializer(many=True, read_only=True)
    
    class Meta:
        model = University
        fields = ['id', 'name', 'country', 'city', 'qs_ranking', 
                  'times_ranking', 'description', 'logo', 'website',
                  'tuition_min', 'tuition_max', 'tuition_currency',
                  'programs', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class UniversityRecommendationSerializer(serializers.ModelSerializer):
    consultant_name = serializers.CharField(source='consultant.username', read_only=True)
    student_name = serializers.CharField(source='student.username', read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    
    class Meta:
        model = UniversityRecommendation
        fields = ['id', 'consultant', 'consultant_name', 'student', 'student_name',
                  'university', 'university_name', 'program', 'program_name',
                  'reason', 'match_score', 'is_viewed', 'created_at']
        read_only_fields = ['id', 'consultant', 'created_at']
    
    def create(self, validated_data):
        validated_data['consultant'] = self.context['request'].user
        return super().create(validated_data)
