from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .decorators import staff_required
from .forms import PatientRegistrationForm
from .models import Appointment, AppointmentSlot, Doctor


def home(request):
    return render(request, "clinic/home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your account has been created.")
            return redirect("home")
    else:
        form = PatientRegistrationForm()

    return render(request, "clinic/register.html", {"form": form})


# ---------- Admin dashboard (staff only) ----------

@staff_required
def dashboard(request):
    context = {
        "doctor_count": Doctor.objects.count(),
        "slot_count": AppointmentSlot.objects.count(),
        "appointment_count": Appointment.objects.filter(status=Appointment.STATUS_CONFIRMED).count(),
        "patient_count": User.objects.filter(is_staff=False).count(),
    }
    return render(request, "clinic/dashboard/home.html", context)