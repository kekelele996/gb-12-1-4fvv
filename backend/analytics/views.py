from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from applications.models import ApplicationProject
from users.models import CustomUser

class ApplicationDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if user.role == 'student':
            applications = ApplicationProject.objects.filter(student=user)
        elif user.role == 'consultant':
            students = [sp.user for sp in user.students.all()]
            applications = ApplicationProject.objects.filter(student__in=students)
        else:
            applications = ApplicationProject.objects.all()
        
        total = applications.count()
        
        status_distribution = applications.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        admitted = applications.filter(status='admitted').count()
        rejected = applications.filter(status='rejected').count()
        submitted = applications.filter(status__in=['submitted', 'waiting']).count()
        
        acceptance_rate = 0
        if admitted + rejected > 0:
            acceptance_rate = round((admitted / (admitted + rejected)) * 100, 2)
        
        countries = applications.values('university__country').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_applications': total,
            'status_distribution': list(status_distribution),
            'admitted_count': admitted,
            'rejected_count': rejected,
            'submitted_count': submitted,
            'acceptance_rate': acceptance_rate,
            'countries_distribution': list(countries),
        })

class ConsultantDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['consultant', 'admin']:
            return Response({'error': 'Permission denied'}, status=403)
        
        if request.user.role == 'consultant':
            students = [sp.user for sp in request.user.students.all()]
        else:
            students = CustomUser.objects.filter(role='student')
        
        total_students = students.count()
        
        student_applications = ApplicationProject.objects.filter(
            student__in=students
        )
        
        status_distribution = student_applications.values('status').annotate(
            count=Count('id')
        )
        
        admitted_total = student_applications.filter(status='admitted').count()
        rejected_total = student_applications.filter(status='rejected').count()
        
        acceptance_rate = 0
        if admitted_total + rejected_total > 0:
            acceptance_rate = round((admitted_total / (admitted_total + rejected_total)) * 100, 2)
        
        return Response({
            'total_students': total_students,
            'total_applications': student_applications.count(),
            'status_distribution': list(status_distribution),
            'admitted_total': admitted_total,
            'rejected_total': rejected_total,
            'acceptance_rate': acceptance_rate,
        })

class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=403)
        
        total_students = CustomUser.objects.filter(role='student').count()
        total_consultants = CustomUser.objects.filter(role='consultant').count()
        total_applications = ApplicationProject.objects.count()
        
        status_distribution = ApplicationProject.objects.values('status').annotate(
            count=Count('id')
        )
        
        admitted_total = ApplicationProject.objects.filter(status='admitted').count()
        rejected_total = ApplicationProject.objects.filter(status='rejected').count()
        
        acceptance_rate = 0
        if admitted_total + rejected_total > 0:
            acceptance_rate = round((admitted_total / (admitted_total + rejected_total)) * 100, 2)
        
        countries = ApplicationProject.objects.values('university__country').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'total_students': total_students,
            'total_consultants': total_consultants,
            'total_applications': total_applications,
            'status_distribution': list(status_distribution),
            'admitted_total': admitted_total,
            'rejected_total': rejected_total,
            'acceptance_rate': acceptance_rate,
            'top_countries': list(countries),
        })
