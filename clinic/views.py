from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import PatientRegistrationForm


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