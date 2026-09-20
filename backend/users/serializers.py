from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile, ConsultantProfile

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'role', 'role_display', 'phone', 'bio', 'date_joined']
        read_only_fields = ['id', 'username', 'date_joined']

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    consultant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'target_country', 'target_degree', 'gpa', 
                  'ielts_score', 'toefl_score', 'gre_score', 'gmat_score',
                  'consultant', 'consultant_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_consultant_name(self, obj):
        return obj.consultant.username if obj.consultant else None

class ConsultantProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    students_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultantProfile
        fields = ['id', 'user', 'specialization', 'experience_years', 
                  'success_cases', 'students_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_students_count(self, obj):
        return obj.user.students.count()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'role', 
                  'first_name', 'last_name', 'phone']
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次输入的密码不一致')
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        if user.role == User.ROLE_STUDENT:
            StudentProfile.objects.create(user=user)
        elif user.role == User.ROLE_CONSULTANT:
            ConsultantProfile.objects.create(user=user)
        
        return user
