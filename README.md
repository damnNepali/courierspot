# Bharosa Courier Services — Full Django Application

Complete courier management system: public website + staff SaaS panel + owner admin panel.
Stack: Django 5/6 · Django REST Framework · SQLite (PostgreSQL-ready) · HTML/CSS/JS.

## Run it (3 commands)

    pip install django djangorestframework qrcode pillow
    python manage.py migrate        # already done — db.sqlite3 ships with demo data
    python manage.py runserver

Open http://127.0.0.1:8000

## Demo logins (password for all: bharosa123)

| Username     | Role                  | Sees                                        |
|--------------|-----------------------|---------------------------------------------|
| owner        | Super Admin (you)     | Everything + Finance/Audit + Branches + Rates|
| manager.ktm  | Branch Admin          | Kathmandu branch operations                 |
| staff.ktm    | Staff                 | Shipments, parcels, expenses (KTM only)     |
| ramesh       | Customer (testpass123)| Their own parcels at /my-parcels/           |

A demo shipment BCS-2026-000001 already exists — try tracking it on the homepage.

## The three ends

PUBLIC WEBSITE (/)            — dark animated site, live tracking, rates from DB,
                                 contact form saved to DB, customer signup/login
STAFF PANEL (/panel/)         — new shipment (auto rate + compulsory NPR 2,000 customs
                                 tax), printable invoice with QR + signature lines,
                                 parcel search, status updates, carrier handover,
                                 expense sheet with bill upload
OWNER PANEL (same /panel/)    — finance (income − expenses = remaining balance,
                                 owner-only), audit log, branches & staff accounts,
                                 rates & restricted items (update the website live)
API                           — GET /api/track/<tracking_id>/ (public, JSON)
Django admin                  — /django-admin/ (developer backstage, login as owner)

## Before going live (production checklist)

1. settings.py: set DEBUG=False, a real SECRET_KEY, ALLOWED_HOSTS, and SITE_URL
   to your real domain (QR codes use it).
2. Switch DATABASES to PostgreSQL; run migrate + seed your real branches/rates.
3. Replace console EMAIL_BACKEND with real SMTP for notifications.
4. Delete demo users, set strong passwords, create your real accounts.
5. Serve behind gunicorn + nginx (or a host like Railway/Render); run
   `python manage.py collectstatic` and serve /media/ properly.

## Where things live

bharosa/        settings & URLs          accounts/   users & roles
core/           rates, restricted, contact   tracking/   parcels, events, QR, API
operations/     branches, invoices, expenses, audit
templates/public/   dark website         templates/panel/   light staff panel
seed.py         demo data script         media/      QR codes & bill uploads
