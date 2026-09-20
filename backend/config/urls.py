from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/universities/', include('universities.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/materials/', include('materials.urls')),
    path('api/timelines/', include('timelines.urls')),
    path('api/messages/', include('messages.urls')),
    path('api/analytics/', include('analytics.urls')),
]
