from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from .models import Appointment, AppointmentSlot, Doctor


class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ["full_name", "specialty", "bio", "is_active"]
        labels = {"is_active": "Currently accepting appointments"}
        help_texts = {"full_name": "Enter the name without \"Dr.\" (e.g. Aria Nguyen)."}
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}


class AppointmentSlotForm(forms.ModelForm):
    class Meta:
        model = AppointmentSlot
        fields = ["doctor", "date", "start_time", "end_time"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "start_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "end_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only offer active doctors (plus the current doctor when editing an existing slot).
        self.fields["doctor"].queryset = Doctor.objects.filter(
            Q(is_active=True) | Q(pk=self.instance.doctor_id)
        ).order_by("full_name")

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        date = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if date and date < timezone.localdate():
            self.add_error("date", "The date cannot be in the past.")

        if start_time and end_time and end_time <= start_time:
            self.add_error("end_time", "End time must be after the start time.")
            return cleaned_data

        if doctor and date and start_time and end_time:
            overlapping = AppointmentSlot.objects.filter(
                doctor=doctor,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise forms.ValidationError("This doctor already has a slot that overlaps with this time.")

        return cleaned_data


class BookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["reason"]
        labels = {"reason": "Reason for visit (optional)"}
        widgets = {"reason": forms.Textarea(attrs={"rows": 3})}


class AppointmentEditForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["slot", "reason"]
        labels = {"slot": "Appointment time", "reason": "Reason for visit (optional)"}
        widgets = {"reason": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Offer every available slot, plus the one this appointment already has.
        available_ids = AppointmentSlot.available().values("pk")
        self.fields["slot"].queryset = (
            AppointmentSlot.objects.filter(Q(pk__in=available_ids) | Q(pk=self.instance.slot_id))
            .select_related("doctor")
            .order_by("date", "start_time")
        )
        self.fields["slot"].empty_label = None