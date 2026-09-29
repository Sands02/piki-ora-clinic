from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),

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
]