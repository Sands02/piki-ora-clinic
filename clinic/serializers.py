
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from .models import Doctor, AppointmentSlot, Appointment


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        return user


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            'id',
            'full_name',
            'specialty',
            'bio',
            'is_active',
        ]


class AppointmentSlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(
        source='doctor.full_name',
        read_only=True
    )

    class Meta:
        model = AppointmentSlot
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'date',
            'start_time',
            'end_time',
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    patient_username = serializers.CharField(
        source='patient.username',
        read_only=True
    )

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'patient_username',
            'slot',
            'status',
            'reason',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'patient',
            'patient_username',
            'status',
            'created_at',
        ]
