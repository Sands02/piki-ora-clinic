from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import patient_required, staff_required
from .forms import (
    AppointmentEditForm,
    AppointmentSlotForm,
    BookingForm,
    DoctorForm,
    PatientRegistrationForm,
)
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


# ---------- Patient pages ----------

def doctors(request):
    doctor_list = (
        Doctor.objects.filter(is_active=True)
        .order_by("full_name")
        .prefetch_related(
            Prefetch("slots", queryset=AppointmentSlot.available(), to_attr="open_slots")
        )
    )
    return render(request, "clinic/doctors.html", {"doctors": doctor_list})


@patient_required
def book_appointment(request, slot_id):
    slot = AppointmentSlot.available().filter(pk=slot_id).first()
    if slot is None:
        messages.error(request, "Sorry, that appointment time is no longer available.")
        return redirect("doctors")

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.slot = slot
            try:
                with transaction.atomic():
                    appointment.save()
            except IntegrityError:
                messages.error(request, "Sorry, someone has just booked that time. Please choose another.")
                return redirect("doctors")
            messages.success(request, f"Your appointment is confirmed: {slot}.")
            return redirect("my_appointments")
    else:
        form = BookingForm()

    return render(request, "clinic/book_appointment.html", {"form": form, "slot": slot})


@patient_required
def my_appointments(request):
    appointments = list(
        request.user.appointments.select_related("slot__doctor").order_by("slot__date", "slot__start_time")
    )
    upcoming = [a for a in appointments if a.is_upcoming]
    history = [a for a in reversed(appointments) if not a.is_upcoming]
    return render(request, "clinic/my_appointments.html", {"upcoming": upcoming, "history": history})


@patient_required
def edit_appointment(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("slot__doctor"), pk=pk, patient=request.user
    )
    if not appointment.is_upcoming:
        messages.error(request, "This appointment can no longer be changed.")
        return redirect("my_appointments")

    if request.method == "POST":
        form = AppointmentEditForm(request.POST, instance=appointment)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                messages.error(request, "Sorry, someone has just booked that time. Please choose another.")
                return redirect("edit_appointment", pk=pk)
            messages.success(request, f"Your appointment has been updated: {appointment.slot}.")
            return redirect("my_appointments")
    else:
        form = AppointmentEditForm(instance=appointment)

    return render(request, "clinic/appointment_form.html", {"form": form, "appointment": appointment})


@patient_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("slot__doctor"), pk=pk, patient=request.user
    )
    if not appointment.is_upcoming:
        messages.error(request, "This appointment can no longer be cancelled.")
        return redirect("my_appointments")

    if request.method == "POST":
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.save(update_fields=["status"])
        messages.success(request, f"Your appointment has been cancelled: {appointment.slot}.")
        return redirect("my_appointments")

    return render(request, "clinic/appointment_confirm_cancel.html", {"appointment": appointment})


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
    doctors_qs = Doctor.objects.order_by("full_name")
    return render(request, "clinic/dashboard/doctor_list.html", {"doctors": doctors_qs})


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