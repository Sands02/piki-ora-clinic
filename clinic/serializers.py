from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from rest_framework import serializers

from .models import Doctor, AppointmentSlot, Appointment


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    # Email is required and must be unique, the same as on the Django registration form.
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
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

    def validate(self, attrs):
        # Same rules as AppointmentSlotForm. On an edit, fields that were not sent keep their current values.
        instance = self.instance
        doctor = attrs.get('doctor', getattr(instance, 'doctor', None))
        date = attrs.get('date', getattr(instance, 'date', None))
        start_time = attrs.get('start_time', getattr(instance, 'start_time', None))
        end_time = attrs.get('end_time', getattr(instance, 'end_time', None))

        if 'doctor' in attrs and not doctor.is_active:
            raise serializers.ValidationError({'doctor': 'This doctor is not accepting appointments.'})

        if date and date < timezone.localdate():
            raise serializers.ValidationError({'date': 'The date cannot be in the past.'})

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({'end_time': 'End time must be after the start time.'})

        overlapping = AppointmentSlot.objects.filter(
            doctor=doctor,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time,
        )
        if instance is not None:
            overlapping = overlapping.exclude(pk=instance.pk)
        if overlapping.exists():
            raise serializers.ValidationError('This doctor already has a slot that overlaps with this time.')

        return attrs


class AppointmentSerializer(serializers.ModelSerializer):
    patient_username = serializers.CharField(
        source='patient.username',
        read_only=True
    )

    # Slot details, so the frontend can show the doctor, date and time instead of a slot ID.
    doctor_name = serializers.CharField(source='slot.doctor.full_name', read_only=True)
    doctor_specialty = serializers.CharField(source='slot.doctor.specialty', read_only=True)
    date = serializers.DateField(source='slot.date', read_only=True)
    start_time = serializers.TimeField(source='slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='slot.end_time', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'patient_username',
            'slot',
            'doctor_name',
            'doctor_specialty',
            'date',
            'start_time',
            'end_time',
            'status',
            'is_upcoming',
            'reason',
            'created_at',
        ]
        # The database constraint still blocks double booking; the views give a clear message instead.
        validators = []
        read_only_fields = [
            'id',
            'patient',
            'patient_username',
            'status',
            'created_at',
        ]


class PatientSerializer(serializers.ModelSerializer):
    """Used by staff to view and update patient accounts."""

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id', 'username', 'date_joined']

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('Another account already uses this email.')
        return value