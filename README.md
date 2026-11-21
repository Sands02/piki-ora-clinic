# Piki Ora Medical Centre – Appointment System

A Django web application that lets patients book and manage appointments with doctors, and lets clinic staff run the clinic through a custom administrator dashboard.

## Live site

| | URL |
|---|---|
| Django application (main site) | https://piki-ora-clinic-rc6k.onrender.com |
| Custom admin dashboard (staff only) | https://piki-ora-clinic-rc6k.onrender.com/dashboard/ |
| React frontend (uses the REST API) | https://piki-ora-frontend-gdnt.onrender.com |

The Render free tier puts the service to sleep when it is not in use, so the first page load can take up to a minute.

> The built-in Django Admin site (`/admin/`) is **not** used to manage the system. All staff features are in the custom dashboard at `/dashboard/`.

## Features

### Patients
- Register and log in
- View active doctors and their available appointment slots
- Book an appointment, with an optional reason for the visit
- See a confirmation message after booking
- View upcoming appointments and past or cancelled ones
- Move an appointment to another free slot, or cancel it

### Administrators (custom dashboard)
- Dashboard overview with counts of doctors, slots, confirmed appointments and patients
- Add, edit and delete doctor profiles, and mark a doctor as not accepting appointments
- Create, edit and delete appointment slots (past dates, end-before-start times and overlapping slots are rejected)
- View all appointments, filtered by confirmed, cancelled or all
- Edit or cancel any appointment
- View patient accounts, update their details, block them from logging in, or delete them

### System
- Patients must be logged in to book
- Double booking is prevented (see below)
- Data is stored in a relational database (PostgreSQL in production, SQLite locally)
- Responsive layout that works on phones and desktops

## Technology

- **Python 3.12**, **Django 5.2**
- **PostgreSQL** on Render (SQLite for local development)
- **Django REST Framework** with token authentication, for the React frontend
- **Gunicorn** and **WhiteNoise** for production on **Render**
- **GitHub** for version control

## Data model

```
User (Django auth) ──< Appointment >── AppointmentSlot >── Doctor
```

- **Doctor**: name, specialty, biography, and whether they are accepting appointments.
- **AppointmentSlot**: a doctor's available time (date, start time, end time). One doctor has many slots.
- **Appointment**: links a patient (`User`) to a slot, with a status (`confirmed` or `cancelled`), a reason and a created timestamp.

Staff and patients are both Django `User` accounts. Staff accounts have `is_staff = True`.

## How double booking is prevented

1. **Database constraint.** `Appointment` has a `UniqueConstraint` on `slot` that only applies when `status = "confirmed"`. The database itself refuses a second confirmed booking for the same slot, while still allowing a slot to be re-booked after a cancellation.
2. **Availability check.** `AppointmentSlot.available()` only returns future slots of active doctors that have no confirmed appointment, so booked slots are never offered.
3. **Safe saving.** Bookings are saved inside `transaction.atomic()`. If two patients submit at the same moment, the second save raises an `IntegrityError`, which is caught and shown as "Sorry, someone has just booked that time."

## Role-based access control

- `@patient_required` (in `clinic/decorators.py`): the page needs a logged-in, non-staff user.
- `@staff_required`: the page needs a logged-in staff user. Everyone else is redirected with an error message.
- Templates show different navigation for visitors, patients and staff.
- Patients can only see and change their own appointments (queries filter by `patient=request.user`).

## Project structure

```
config/
  settings.py        Settings (database, security, static files, REST framework)
  urls.py            Top-level URLs
clinic/
  models.py          Doctor, AppointmentSlot, Appointment
  forms.py           Registration, booking, editing and dashboard forms with validation
  views.py           Patient pages and the custom admin dashboard
  decorators.py      staff_required and patient_required
  urls.py            Website URLs
  api_views.py       REST API used by the React frontend
  serializers.py     REST API serializers
  api_urls.py        REST API URLs
  templates/
    clinic/          Patient pages and base layout
    clinic/dashboard/  Custom admin dashboard pages
    registration/    Login page
build.sh             Render build script
requirements.txt     Python dependencies
```

## Running locally

```bash
git clone https://github.com/Sands02/piki-ora-clinic.git
cd piki-ora-clinic

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # this account can use /dashboard/
python manage.py runserver
```

Then open http://127.0.0.1:8000. Without a `DATABASE_URL` environment variable, the app uses a local SQLite database (`db.sqlite3`).

## Deployment (Render)

The app is deployed as a Render **Web Service** connected to this repository, with a Render **PostgreSQL** database in the same region.

- **Build command:** `bash build.sh` (installs packages, collects static files, runs migrations and creates the admin account)
- **Start command:** `gunicorn config.wsgi:application`

Environment variables on the web service:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Internal connection URL of the Render PostgreSQL database |
| `SECRET_KEY` | Django secret key (long random value, never committed) |
| `DJANGO_SUPERUSER_USERNAME` / `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` | Creates the first staff account during the build |

Render sets `RENDER` automatically. The settings use it to turn debug mode off, require the secret key from the environment, and send cookies only over HTTPS.

## REST API (used by the React frontend)

| Method and path | Who | Purpose |
|---|---|---|
| `POST /api/register/` | Anyone | Create a patient account |
| `POST /api/token/` | Anyone | Log in and receive a token |
| `GET /api/me/` | Logged in | Current user and whether they are staff |
| `GET /api/doctors/` | Anyone | List doctors (staff can also add or edit) |
| `GET /api/slots/` | Anyone | List available slots (staff can also add or edit) |
| `GET /api/appointments/` | Logged in | Own appointments (staff see all) |
| `POST /api/appointments/` | Logged in | Book a slot |
| `POST /api/appointments/<id>/cancel/` | Logged in | Cancel an appointment |

Requests send the token in the header `Authorization: Token <token>`.