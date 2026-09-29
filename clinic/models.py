from django.db import models
from django.utils import timezone


class Doctor(models.Model):
    full_name = models.CharField(max_length=150)
    specialty = models.CharField(max_length=150)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.full_name} ({self.specialty})"


class AppointmentSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"Dr. {self.doctor.full_name}, {self.date:%a %d %b %Y}, {self.start_time:%I:%M %p}"

    @classmethod
    def available(cls):
        """Future slots of active doctors that do not have a confirmed appointment."""
        now = timezone.localtime()
        booked = Appointment.objects.filter(
            slot=models.OuterRef("pk"), status=Appointment.STATUS_CONFIRMED
        )
        return (
            cls.objects.filter(doctor__is_active=True)
            .filter(models.Q(date__gt=now.date()) | models.Q(date=now.date(), start_time__gt=now.time()))
            .filter(~models.Exists(booked))
            .select_related("doctor")
            .order_by("date", "start_time")
        )


class Appointment(models.Model):
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    patient = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="appointments"
    )
    slot = models.ForeignKey(
        AppointmentSlot, on_delete=models.CASCADE, related_name="appointments"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["slot"],
                condition=models.Q(status="confirmed"),
                name="unique_confirmed_appointment_per_slot",
            )
        ]

    def __str__(self):
        return f"{self.patient.username} with {self.slot} ({self.status})"

    @property
    def is_upcoming(self):
        """True if the appointment is confirmed and has not started yet."""
        now = timezone.localtime()
        slot = self.slot
        return self.status == self.STATUS_CONFIRMED and (
            slot.date > now.date() or (slot.date == now.date() and slot.start_time > now.time())
        )