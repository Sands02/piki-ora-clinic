from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Doctor, AppointmentSlot, Appointment
from .permissions import IsAdminOrReadOnly
from .serializers import (
    DoctorSerializer,
    AppointmentSlotSerializer,
    AppointmentSerializer,
    PatientSerializer,
)


User = get_user_model()


class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        doctors = Doctor.objects.order_by('full_name')

        if not self.request.user.is_staff:
            doctors = doctors.filter(is_active=True)

        return doctors


class AppointmentSlotViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSlotSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_staff:
            return AppointmentSlot.objects.select_related('doctor').order_by('date', 'start_time')

        return AppointmentSlot.available()


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        appointments = Appointment.objects.select_related(
            'patient', 'slot', 'slot__doctor'
        ).order_by('slot__date', 'slot__start_time')

        if self.request.user.is_staff:
            return appointments

        return appointments.filter(patient=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            raise PermissionDenied('Staff accounts cannot book appointments.')

        slot = serializer.validated_data['slot']

        if not AppointmentSlot.available().filter(pk=slot.pk).exists():
            raise ValidationError({
                'slot': 'This appointment slot is no longer available.'
            })

        try:
            with transaction.atomic():
                serializer.save(patient=self.request.user)
        except IntegrityError:
            raise ValidationError({
                'slot': 'This appointment slot has already been booked.'
            })

    def perform_update(self, serializer):
        appointment = serializer.instance

        if not self.request.user.is_staff and not appointment.is_upcoming:
            raise ValidationError('This appointment can no longer be changed.')

        new_slot = serializer.validated_data.get('slot', appointment.slot)

        if new_slot != appointment.slot:
            if not AppointmentSlot.available().filter(pk=new_slot.pk).exists():
                raise ValidationError({
                    'slot': 'This appointment slot is no longer available.'
                })

        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError:
            raise ValidationError({
                'slot': 'This appointment slot has already been booked.'
            })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()

        if appointment.status == Appointment.STATUS_CANCELLED:
            return Response(
                {'detail': 'Appointment is already cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.is_staff and not appointment.is_upcoming:
            return Response(
                {'detail': 'This appointment can no longer be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = Appointment.STATUS_CANCELLED
        appointment.save(update_fields=['status'])

        return Response(
            {'detail': 'Appointment cancelled successfully.'},
            status=status.HTTP_200_OK
        )


class PatientViewSet(viewsets.ModelViewSet):

    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAdminUser]

    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return User.objects.filter(is_staff=False).order_by('last_name', 'first_name', 'username')
