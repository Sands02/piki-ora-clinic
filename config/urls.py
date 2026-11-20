
from django.contrib import admin
from django.urls import include, path

from rest_framework.authtoken.views import obtain_auth_token

from clinic.api_views import CurrentUserView


urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/', include('django.contrib.auth.urls')),

    # Authentication
    path('api/token/', obtain_auth_token, name='api_token'),
    path('api/me/', CurrentUserView.as_view(), name='current_user'),

    # Clinic API
    path('api/', include('clinic.api_urls')),

    # Existing clinic website
    path('', include('clinic.urls')),
]
