from django.urls import path
from .views import ApplicationDashboardView, ConsultantDashboardView, AdminDashboardView

urlpatterns = [
    path('dashboard/applications/', ApplicationDashboardView.as_view(), name='application-dashboard'),
    path('dashboard/consultant/', ConsultantDashboardView.as_view(), name='consultant-dashboard'),
    path('dashboard/admin/', AdminDashboardView.as_view(), name='admin-dashboard'),
]
