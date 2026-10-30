# 🚀 LeadRadar AI — Intelligent B2B Lead & Opportunity Engine

A production-ready SaaS application built with **Django**, **SQLite (`db.sqlite3`)**, **Tailwind CSS**, and **Alpine.js**.

---

## 🏗️ Architecture & Modules

```
lead_radar/ (C:\Lead-Generate)
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py           # Core settings with db.sqlite3 & installed apps
│   │   ├── development.py    # Local dev settings
│   │   └── production.py     # Production settings
│   ├── urls.py               # Central routing
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/             # Custom User, Multi-tenant Workspace & Memberships
│   ├── dashboard/            # SaaS Dashboard & Pipeline metrics
│   ├── leads/                # Lead Directory, CSV Importer, Lead Discovery Engine
│   ├── scanner/              # Real HTTP & Smart Fallback Website Health Auditor
│   ├── opportunities/        # Deterministic 100-pt Rule-Based Opportunity Engine
│   ├── ai_engine/            # Cold Outreach Pitch Generator (Gemini API + Smart Heuristic)
│   ├── crm/                  # Visual Kanban Board, Activity Notes & Scheduled Follow-ups
│   ├── outreach/             # Cold Outreach Campaigns & Review/Approval Queues
│   ├── proposals/            # Client Quotations & Printable Proposals
│   └── reports/              # Conversion Funnel & Industry Analytics
├── templates/                # Modular Django Templates + Tailwind CSS + Alpine.js
├── static/                   # Static CSS & JS assets
├── requirements.txt
├── sample_leads.csv          # Sample CSV for quick testing
├── .env
└── db.sqlite3
```

---

## ⚡ Quick Start

### 1. Activate Virtual Environment
```powershell
cd C:\Lead-Generate
.\venv\Scripts\Activate.ps1
```

### 2. Run Database Migrations
```powershell
python manage.py makemigrations accounts leads scanner opportunities ai_engine crm outreach proposals reports
python manage.py migrate
```

### 3. Create Superuser (Admin)
```powershell
python manage.py createsuperuser
```

### 4. Start Development Server
```powershell
python manage.py runserver
```
Visit: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🌟 Key Highlights & Verification

1. **Deterministic Opportunity Scoring (0 - 100):**
   - Missing WhatsApp CTA: `+15`
   - No Online Ordering: `+20`
   - No Online Booking: `+15`
   - Missing Meta Description / Poor SEO: `+15`
   - Insecure / Missing SSL: `+15`
   - Broken Links / Technical issues: `+10`
   - Mobile Unresponsive: `+10`
   *(Score >= 70 = High Opportunity, 40-69 = Medium, <40 = Low)*

2. **AI Outreach Engine:**
   - Works immediately out of the box with intelligent consultative pitch templates.
   - If you set `GEMINI_API_KEY` in `.env`, it connects to Google Gemini 2.5 Flash for dynamic generation!

3. **Multi-Tenant Foundation:**
   - Every lead, campaign, audit, and proposal is strictly scoped to the active tenant's `Workspace`.
