from django.db import models


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
        return f"{self.doctor.full_name}: {self.date} {self.start_time}-{self.end_time}"


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