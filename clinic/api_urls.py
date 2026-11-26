from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import RegisterView
from .viewsets import (
    DoctorViewSet,
    AppointmentSlotViewSet,
    AppointmentViewSet,
    PatientViewSet,
)


router = DefaultRouter()

router.register('doctors', DoctorViewSet, basename='doctor')
router.register('slots', AppointmentSlotViewSet, basename='slot')
router.register('appointments', AppointmentViewSet, basename='appointment')
router.register('patients', PatientViewSet, basename='patient')


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
]
