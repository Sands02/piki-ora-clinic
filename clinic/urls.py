from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),

    # Patient pages
    path("doctors/", views.doctors, name="doctors"),
    path("book/<int:slot_id>/", views.book_appointment, name="book_appointment"),
    path("my-appointments/", views.my_appointments, name="my_appointments"),
    path("my-appointments/<int:pk>/edit/", views.edit_appointment, name="edit_appointment"),
    path("my-appointments/<int:pk>/cancel/", views.cancel_appointment, name="cancel_appointment"),

    # Admin dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    path("dashboard/doctors/", views.doctor_list, name="doctor_list"),
    path("dashboard/doctors/add/", views.doctor_create, name="doctor_create"),
    path("dashboard/doctors/<int:pk>/edit/", views.doctor_edit, name="doctor_edit"),
    path("dashboard/doctors/<int:pk>/delete/", views.doctor_delete, name="doctor_delete"),

    path("dashboard/slots/", views.slot_list, name="slot_list"),
    path("dashboard/slots/add/", views.slot_create, name="slot_create"),
    path("dashboard/slots/<int:pk>/edit/", views.slot_edit, name="slot_edit"),
    path("dashboard/slots/<int:pk>/delete/", views.slot_delete, name="slot_delete"),

    path("dashboard/appointments/", views.appointment_list, name="appointment_list"),
    path("dashboard/appointments/<int:pk>/edit/", views.admin_appointment_edit, name="admin_appointment_edit"),
    path("dashboard/appointments/<int:pk>/cancel/", views.admin_appointment_cancel, name="admin_appointment_cancel"),

    path("dashboard/patients/", views.patient_list, name="patient_list"),
    path("dashboard/patients/<int:pk>/edit/", views.patient_edit, name="patient_edit"),
    path("dashboard/patients/<int:pk>/delete/", views.patient_delete, name="patient_delete"),
]