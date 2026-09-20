from django.urls import path
from .views import (
    CustomTokenObtainPairView, RegisterView, 
    CurrentUserView, StudentProfileView, 
    ConsultantProfileView, ConsultantListView
)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('profile/student/', StudentProfileView.as_view(), name='student_profile'),
    path('profile/consultant/', ConsultantProfileView.as_view(), name='consultant_profile'),
    path('consultants/', ConsultantListView.as_view(), name='consultant_list'),
]
