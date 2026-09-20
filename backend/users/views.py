from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .models import StudentProfile, ConsultantProfile
from .serializers import (
    RegisterSerializer, UserSerializer, 
    StudentProfileSerializer, ConsultantProfileSerializer
)

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        user = User.objects.get(username=request.data.get('username'))
        response.data['user'] = UserSerializer(user).data
        return response

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': '注册成功',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        profile, created = StudentProfile.objects.get_or_create(user=request.user)
        serializer = StudentProfileSerializer(profile)
        return Response(serializer.data)
    
    def put(self, request):
        profile, created = StudentProfile.objects.get_or_create(user=request.user)
        serializer = StudentProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConsultantProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != User.ROLE_CONSULTANT:
            return Response({'error': '只有顾问可以访问此资源'}, status=status.HTTP_403_FORBIDDEN)
        
        profile, created = ConsultantProfile.objects.get_or_create(user=request.user)
        serializer = ConsultantProfileSerializer(profile)
        return Response(serializer.data)
    
    def put(self, request):
        if request.user.role != User.ROLE_CONSULTANT:
            return Response({'error': '只有顾问可以访问此资源'}, status=status.HTTP_403_FORBIDDEN)
        
        profile, created = ConsultantProfile.objects.get_or_create(user=request.user)
        serializer = ConsultantProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConsultantListView(generics.ListAPIView):
    queryset = User.objects.filter(role=User.ROLE_CONSULTANT)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
