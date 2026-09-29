from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import staff_required
from .forms import AppointmentSlotForm, DoctorForm, PatientRegistrationForm
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


# ---------- Dashboard: doctors ----------

@staff_required
def doctor_list(request):
    doctors = Doctor.objects.order_by("full_name")
    return render(request, "clinic/dashboard/doctor_list.html", {"doctors": doctors})


@staff_required
def doctor_create(request):
    if request.method == "POST":
        form = DoctorForm(request.POST)
        if form.is_valid():
            doctor = form.save()
            messages.success(request, f"Dr. {doctor.full_name} has been added.")
            return redirect("doctor_list")
    else:
        form = DoctorForm()

    return render(request, "clinic/dashboard/doctor_form.html", {"form": form, "title": "Add doctor"})


@staff_required
def doctor_edit(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)

    if request.method == "POST":
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dr. {doctor.full_name} has been updated.")
            return redirect("doctor_list")
    else:
        form = DoctorForm(instance=doctor)

    return render(request, "clinic/dashboard/doctor_form.html", {"form": form, "title": "Edit doctor"})


@staff_required
def doctor_delete(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)

    if request.method == "POST":
        name = doctor.full_name
        doctor.delete()
        messages.success(request, f"Dr. {name} has been removed.")
        return redirect("doctor_list")

    return render(request, "clinic/dashboard/doctor_confirm_delete.html", {"doctor": doctor})


# ---------- Dashboard: appointment slots ----------

@staff_required
def slot_list(request):
    confirmed_booking = Appointment.objects.filter(
        slot=OuterRef("pk"), status=Appointment.STATUS_CONFIRMED
    )
    slots = (
        AppointmentSlot.objects.filter(date__gte=timezone.localdate())
        .select_related("doctor")
        .annotate(is_booked=Exists(confirmed_booking))
        .order_by("date", "start_time")
    )
    return render(request, "clinic/dashboard/slot_list.html", {"slots": slots})


@staff_required
def slot_create(request):
    if request.method == "POST":
        form = AppointmentSlotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "The appointment slot has been created.")
            return redirect("slot_list")
    else:
        form = AppointmentSlotForm()

    return render(request, "clinic/dashboard/slot_form.html", {"form": form, "title": "Add appointment slot"})


@staff_required
def slot_edit(request, pk):
    slot = get_object_or_404(AppointmentSlot, pk=pk)

    if request.method == "POST":
        form = AppointmentSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, "The appointment slot has been updated.")
            return redirect("slot_list")
    else:
        form = AppointmentSlotForm(instance=slot)

    return render(request, "clinic/dashboard/slot_form.html", {"form": form, "title": "Edit appointment slot"})


@staff_required
def slot_delete(request, pk):
    slot = get_object_or_404(AppointmentSlot.objects.select_related("doctor"), pk=pk)

    if request.method == "POST":
        slot.delete()
        messages.success(request, "The appointment slot has been deleted.")
        return redirect("slot_list")

    return render(request, "clinic/dashboard/slot_confirm_delete.html", {"slot": slot})