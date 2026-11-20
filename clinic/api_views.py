
from django.db import IntegrityError, transaction

from rest_framework import (
    viewsets,
    permissions,
    status,
    generics,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from .models import Doctor, AppointmentSlot, Appointment
from .serializers import (
    DoctorSerializer,
    AppointmentSlotSerializer,
    AppointmentSerializer,
    RegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'is_staff': request.user.is_staff,
        })


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated
            and request.user.is_staff
        )


class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        doctors = Doctor.objects.all()

        if not self.request.user.is_staff:
            doctors = doctors.filter(is_active=True)

        return doctors


class AppointmentSlotViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSlotSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_staff:
            return AppointmentSlot.objects.select_related('doctor').all()

        return AppointmentSlot.available()


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        appointments = Appointment.objects.select_related(
            'patient', 'slot', 'slot__doctor'
        )

        if self.request.user.is_staff:
            return appointments.all()

        return appointments.filter(patient=self.request.user)

    def perform_create(self, serializer):
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
        appointment = self.get_object()
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
                {'message': 'Appointment is already cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = Appointment.STATUS_CANCELLED
        appointment.save(update_fields=['status'])

        return Response(
            {'message': 'Appointment cancelled successfully.'},
            status=status.HTTP_200_OK
        )
