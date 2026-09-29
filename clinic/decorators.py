from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def staff_required(view_func):
    """Allow only logged-in staff users; send everyone else away."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You do not have permission to access the admin dashboard.")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return wrapper


def patient_required(view_func):
    """Allow only logged-in patients (non-staff users)."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff:
            messages.error(request, "Staff accounts manage appointments from the admin dashboard.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper