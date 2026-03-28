# Complaint Management System v2 — Upgraded

## What's New in This Version
- ✅ **Forgot Password** — Token-based reset via email (30-min expiry, one-time use)
- ✅ **Registration Email** — Welcome email sent automatically on signup
- ✅ **Professional UI** — Soft, eye-friendly dark theme (no harsh neons)
- ✅ **Consistent Design** — All 7 pages use the same `Plus Jakarta Sans` font & color system
- ✅ **Page Transitions** — Smooth fade in/out between all pages
- ✅ **Staggered Animations** — Cards, stats, and complaint items animate in sequence

---

## Quick Start

```bash
pip install flask pymongo
mongod               # start MongoDB locally
python app.py        # visit http://localhost:5000
```

---

## Email Setup (Required for Forgot Password & Welcome Emails)

Set these environment variables before running:

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your_email@gmail.com
export SMTP_PASS=your_google_app_password   # NOT your main password
export APP_BASE_URL=http://localhost:5000    # change for production
```

### Getting a Gmail App Password
1. Go to Google Account → Security → 2-Step Verification (enable it)
2. Then go to → App Passwords
3. Create a new App Password → select "Mail" → copy the 16-char password
4. Use that as `SMTP_PASS`

> **Note:** If email is not configured, the app still works fully — emails simply won't send (errors are logged to console only).

---

## Pages & Routes

| Route | Description |
|---|---|
| `/` | Login (User + Admin tabs) |
| `/register_page` | Registration with welcome email |
| `/forgot_password` | Request password reset link |
| `/reset_password/<token>` | Set new password via emailed link |
| `/user_dashboard` | Submit & track complaints |
| `/admin_dashboard` | Department admin view |
| `/super_admin` | Super admin — all departments + stats |

---

## Admin Accounts (Auto-Created on First Run)

| Role | Email | Password |
|---|---|---|
| 👑 Super Admin | admin@cms.com | admin123 |
| 🏠 Hostel Admin | hostel.admin@cms.com | hostel@123 |
| 💰 Finance Admin | finance.admin@cms.com | finance@123 |
| 🚌 Transport Admin | transport.admin@cms.com | transport@123 |
| 📚 Academic Admin | academic.admin@cms.com | academic@123 |
| 💻 IT Admin | itsupport.admin@cms.com | itsupport@123 |
| 🏗️ Infra Admin | infra.admin@cms.com | infra@123 |
| 📖 Library Admin | library.admin@cms.com | library@123 |
| 🏥 Medical Admin | medical.admin@cms.com | medical@123 |
| ⚽ Sports Admin | sports.admin@cms.com | sports@123 |
| 🍽️ Canteen Admin | canteen.admin@cms.com | canteen@123 |
| 📌 General Admin | general.admin@cms.com | general@123 |

---

## MongoDB Collections
- `users` — all accounts (students, admins, super admin)
- `complaints` — all complaint records
- `password_reset_tokens` — one-time reset tokens (auto-cleaned on use)
