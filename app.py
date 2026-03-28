from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime, os, secrets, smtplib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "cms_v2_secure_2026"

# ── Upload Config ────────────────────────────────────────────────────
UPLOAD_FOLDER    = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── MongoDB ──────────────────────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client     = MongoClient(MONGO_URI)
db         = client["complaint_system_v2"]
users_col      = db["users"]
complaints_col = db["complaints"]
tokens_col     = db["password_reset_tokens"]

# ── Email Config (set these env vars or edit directly) ───────────────
SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER     = os.environ.get("SMTP_USER", "your_email@gmail.com")
SMTP_PASS     = os.environ.get("SMTP_PASS", "your_app_password")
APP_BASE_URL  = os.environ.get("APP_BASE_URL", "http://localhost:5000")

# ── Email Helper ─────────────────────────────────────────────────────
def send_email(to_email, subject, html_body):
    """Send HTML email via SMTP. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"ComplaintMS <{SMTP_USER}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

def send_welcome_email(name, email):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f6fa;font-family:'Segoe UI',sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6fa;padding:40px 0;">
        <tr><td align="center">
          <table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
            <tr>
              <td style="background:linear-gradient(135deg,#3b5bdb,#6741d9);padding:36px 40px;text-align:center;">
                <div style="background:rgba(255,255,255,0.15);display:inline-block;padding:14px 18px;border-radius:12px;font-size:28px;margin-bottom:16px;">📋</div>
                <h1 style="color:#fff;margin:0;font-size:22px;font-weight:700;letter-spacing:-0.02em;">Welcome to ComplaintMS</h1>
                <p style="color:rgba(255,255,255,0.75);margin:8px 0 0;font-size:14px;">Your account has been created successfully</p>
              </td>
            </tr>
            <tr>
              <td style="padding:36px 40px;">
                <p style="color:#374151;font-size:16px;margin:0 0 16px;">Hi <strong>{name}</strong>,</p>
                <p style="color:#6b7280;font-size:14px;line-height:1.7;margin:0 0 24px;">
                  Your account has been registered on the Complaint Management System. You can now log in and submit complaints — they'll be automatically routed to the right department.
                </p>
                <div style="background:#f8f9ff;border:1px solid #e5e7ff;border-radius:12px;padding:20px;margin-bottom:24px;">
                  <p style="color:#374151;font-size:13px;font-weight:600;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.05em;">Your Registered Email</p>
                  <p style="color:#3b5bdb;font-size:15px;font-weight:700;margin:0;">{email}</p>
                </div>
                <div style="text-align:center;margin-bottom:24px;">
                  <a href="{APP_BASE_URL}" style="background:linear-gradient(135deg,#3b5bdb,#6741d9);color:#fff;text-decoration:none;padding:14px 32px;border-radius:10px;font-size:14px;font-weight:600;display:inline-block;">
                    Sign In to Dashboard →
                  </a>
                </div>
                <p style="color:#9ca3af;font-size:12px;text-align:center;margin:0;">
                  If you didn't create this account, please ignore this email.
                </p>
              </td>
            </tr>
            <tr>
              <td style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #f3f4f6;">
                <p style="color:#9ca3af;font-size:12px;margin:0;">© 2026 ComplaintMS · All rights reserved</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    send_email(email, "Welcome to ComplaintMS — Account Created ✅", html)

def send_reset_email(name, email, token):
    reset_link = f"{APP_BASE_URL}/reset_password/{token}"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f6fa;font-family:'Segoe UI',sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6fa;padding:40px 0;">
        <tr><td align="center">
          <table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
            <tr>
              <td style="background:linear-gradient(135deg,#d97706,#b45309);padding:36px 40px;text-align:center;">
                <div style="background:rgba(255,255,255,0.15);display:inline-block;padding:14px 18px;border-radius:12px;font-size:28px;margin-bottom:16px;">🔐</div>
                <h1 style="color:#fff;margin:0;font-size:22px;font-weight:700;letter-spacing:-0.02em;">Password Reset Request</h1>
                <p style="color:rgba(255,255,255,0.75);margin:8px 0 0;font-size:14px;">This link expires in 30 minutes</p>
              </td>
            </tr>
            <tr>
              <td style="padding:36px 40px;">
                <p style="color:#374151;font-size:16px;margin:0 0 16px;">Hi <strong>{name}</strong>,</p>
                <p style="color:#6b7280;font-size:14px;line-height:1.7;margin:0 0 24px;">
                  We received a request to reset the password for your ComplaintMS account. Click the button below to set a new password. This link will expire in <strong>30 minutes</strong>.
                </p>
                <div style="text-align:center;margin-bottom:24px;">
                  <a href="{reset_link}" style="background:linear-gradient(135deg,#d97706,#b45309);color:#fff;text-decoration:none;padding:14px 32px;border-radius:10px;font-size:14px;font-weight:600;display:inline-block;">
                    Reset My Password →
                  </a>
                </div>
                <div style="background:#fff8e6;border:1px solid #fde68a;border-radius:10px;padding:16px;margin-bottom:20px;">
                  <p style="color:#92400e;font-size:13px;margin:0;">⚠️ If you didn't request this, you can safely ignore this email. Your password won't change.</p>
                </div>
                <p style="color:#9ca3af;font-size:12px;text-align:center;margin:0;">
                  Or copy this link: <span style="color:#d97706;">{reset_link}</span>
                </p>
              </td>
            </tr>
            <tr>
              <td style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #f3f4f6;">
                <p style="color:#9ca3af;font-size:12px;margin:0;">© 2026 ComplaintMS · Security Team</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    send_email(email, "Reset Your ComplaintMS Password 🔐", html)

# ── Category → Admin Routing Map ────────────────────────────────────
CATEGORY_ADMINS = {
    "Hostel":         {"email": "hostel.admin@cms.com",    "password": "hostel@123",    "name": "Hostel Admin"},
    "Fee / Finance":  {"email": "finance.admin@cms.com",   "password": "finance@123",   "name": "Finance Admin"},
    "Transport":      {"email": "transport.admin@cms.com", "password": "transport@123", "name": "Transport Admin"},
    "Academic":       {"email": "academic.admin@cms.com",  "password": "academic@123",  "name": "Academic Admin"},
    "IT Support":     {"email": "itsupport.admin@cms.com", "password": "itsupport@123", "name": "IT Support Admin"},
    "Infrastructure": {"email": "infra.admin@cms.com",     "password": "infra@123",     "name": "Infrastructure Admin"},
    "Library":        {"email": "library.admin@cms.com",   "password": "library@123",   "name": "Library Admin"},
    "Medical":        {"email": "medical.admin@cms.com",   "password": "medical@123",   "name": "Medical Admin"},
    "Sports":         {"email": "sports.admin@cms.com",    "password": "sports@123",    "name": "Sports Admin"},
    "Canteen":        {"email": "canteen.admin@cms.com",   "password": "canteen@123",   "name": "Canteen Admin"},
    "Other":          {"email": "general.admin@cms.com",   "password": "general@123",   "name": "General Admin"},
}

CATEGORIES = list(CATEGORY_ADMINS.keys())

CATEGORY_ICONS = {
    "Hostel": "🏠", "Fee / Finance": "💰", "Transport": "🚌",
    "Academic": "📚", "IT Support": "💻", "Infrastructure": "🏗️",
    "Library": "📖", "Medical": "🏥", "Sports": "⚽",
    "Canteen": "🍽️", "Other": "📌",
}

SUPER_ADMIN = {"email": "admin@cms.com", "password": "admin123", "name": "Super Admin", "role": "SuperAdmin"}

# ── Seed Accounts ────────────────────────────────────────────────────
def seed_accounts():
    if not users_col.find_one({"email": SUPER_ADMIN["email"]}):
        users_col.insert_one({**SUPER_ADMIN, "created_at": datetime.datetime.now()})
    for cat, info in CATEGORY_ADMINS.items():
        if not users_col.find_one({"email": info["email"]}):
            users_col.insert_one({
                "name": info["name"], "email": info["email"],
                "password": info["password"], "role": "Admin",
                "category": cat, "created_at": datetime.datetime.now()
            })

seed_accounts()

# ── Helpers ──────────────────────────────────────────────────────────
def get_complaint_categories(complaint):
    cats = [complaint.get("primary_category", "")]
    sec = complaint.get("secondary_category", "")
    if sec and sec != "None": cats.append(sec)
    return cats

def admin_can_see(admin_user, complaint):
    if admin_user.get("role") == "SuperAdmin": return True
    return admin_user.get("category", "") in get_complaint_categories(complaint)

# ── Auth Routes ──────────────────────────────────────────────────────
@app.route('/')
def login_page():
    if 'user' in session:
        role = session.get('role')
        if role == 'SuperAdmin': return redirect(url_for('super_admin'))
        if role == 'Admin':      return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return render_template('login.html', categories=CATEGORIES, category_icons=CATEGORY_ICONS)

@app.route('/register_page')
def register_page():
    return render_template('register.html')

@app.route('/register_action', methods=['POST'])
def register_action():
    name     = request.form.get('name', '').strip()
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    if users_col.find_one({"email": email}):
        flash("Email already registered.", "danger")
        return redirect(url_for('register_page'))
    users_col.insert_one({
        "name": name, "email": email, "password": password,
        "role": "Client", "created_at": datetime.datetime.now()
    })
    # Send welcome email (non-blocking)
    send_welcome_email(name, email)
    flash("Account created! A confirmation email has been sent. Please login.", "success")
    return redirect(url_for('login_page'))

@app.route('/login_action', methods=['POST'])
def login_action():
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    if email == SUPER_ADMIN["email"] and password == SUPER_ADMIN["password"]:
        session['user']     = SUPER_ADMIN["name"]
        session['role']     = "SuperAdmin"
        session['email']    = SUPER_ADMIN["email"]
        session['category'] = None
        return redirect(url_for('super_admin'))
    user = users_col.find_one({"email": email, "password": password})
    if user:
        session['user']     = user['name']
        session['role']     = user['role']
        session['email']    = user['email']
        session['uid']      = str(user['_id'])
        session['category'] = user.get('category')
        if user['role'] == 'Admin':      return redirect(url_for('admin_dashboard'))
        if user['role'] == 'SuperAdmin': return redirect(url_for('super_admin'))
        return redirect(url_for('user_dashboard'))
    flash("Invalid credentials. Please check your email and password.", "danger")
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ── Forgot Password Routes ───────────────────────────────────────────
@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/forgot_password_action', methods=['POST'])
def forgot_password_action():
    email = request.form.get('email', '').strip().lower()
    user  = users_col.find_one({"email": email})
    # Always show the same message (security best practice)
    flash("If that email is registered, a reset link has been sent.", "success")
    if user:
        token = secrets.token_urlsafe(48)
        tokens_col.delete_many({"email": email})  # invalidate old tokens
        tokens_col.insert_one({
            "email":      email,
            "token":      token,
            "created_at": datetime.datetime.now(),
            "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=30),
            "used":       False
        })
        send_reset_email(user['name'], email, token)
    return redirect(url_for('forgot_password'))

@app.route('/reset_password/<token>')
def reset_password(token):
    record = tokens_col.find_one({"token": token, "used": False})
    if not record or record['expires_at'] < datetime.datetime.now():
        flash("This reset link has expired or is invalid. Please request a new one.", "danger")
        return redirect(url_for('forgot_password'))
    return render_template('reset_password.html', token=token)

@app.route('/reset_password_action', methods=['POST'])
def reset_password_action():
    token    = request.form.get('token', '')
    password = request.form.get('password', '')
    confirm  = request.form.get('confirm_password', '')
    if password != confirm:
        flash("Passwords do not match.", "danger")
        return redirect(url_for('reset_password', token=token))
    if len(password) < 6:
        flash("Password must be at least 6 characters.", "danger")
        return redirect(url_for('reset_password', token=token))
    record = tokens_col.find_one({"token": token, "used": False})
    if not record or record['expires_at'] < datetime.datetime.now():
        flash("This reset link has expired. Please request a new one.", "danger")
        return redirect(url_for('forgot_password'))
    users_col.update_one({"email": record['email']}, {"$set": {"password": password}})
    tokens_col.update_one({"token": token}, {"$set": {"used": True}})
    flash("Password updated successfully! Please sign in.", "success")
    return redirect(url_for('login_page'))

# ── User Routes ──────────────────────────────────────────────────────
@app.route('/user_dashboard')
def user_dashboard():
    if 'user' not in session or session.get('role') not in ('Client',):
        return redirect(url_for('login_page'))
    my = list(complaints_col.find({"email": session['email']}).sort("created_at", -1))
    stats = {
        "total":      len(my),
        "pending":    sum(1 for c in my if c['status'] == 'Pending'),
        "inprogress": sum(1 for c in my if c['status'] == 'In Progress'),
        "resolved":   sum(1 for c in my if c['status'] == 'Resolved'),
    }
    return render_template('index.html', complaints=my, stats=stats,
                           categories=CATEGORIES, category_icons=CATEGORY_ICONS)

@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    if 'user' not in session: return redirect(url_for('login_page'))
    primary   = request.form.get('primary_category', '')
    secondary = request.form.get('secondary_category', 'None')
    if secondary == primary: secondary = 'None'

    # ── Photo / Proof Upload ─────────────────────────────────────────
    photo_filename = None
    if 'proof_photo' in request.files:
        file = request.files['proof_photo']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{int(time.time())}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_filename = filename
    # ────────────────────────────────────────────────────────────────

    complaints_col.insert_one({
        "name":               session['user'],
        "email":              session['email'],
        "subject":            request.form.get('subject', '').strip(),
        "primary_category":   primary,
        "secondary_category": secondary,
        "description":        request.form.get('description', '').strip(),
        "proof_photo":        photo_filename,
        "status":             "Pending",
        "created_at":         datetime.datetime.now(),
        "date":               datetime.datetime.now().strftime("%d %b %Y, %H:%M"),
        "assigned_admins":    [CATEGORY_ADMINS[primary]["email"]] +
                              ([CATEGORY_ADMINS[secondary]["email"]] if secondary != 'None' and secondary in CATEGORY_ADMINS else []),
        "admin_response":     "",
    })
    flash("Complaint submitted and routed to the right department!", "success")
    return redirect(url_for('user_dashboard'))

# ── Category Admin Dashboard ─────────────────────────────────────────
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'Admin': return redirect(url_for('login_page'))
    admin_cat = session.get('category')
    my_complaints = list(complaints_col.find({
        "$or": [{"primary_category": admin_cat}, {"secondary_category": admin_cat}]
    }).sort("created_at", -1))
    stats = {
        "total":      len(my_complaints),
        "pending":    sum(1 for c in my_complaints if c['status'] == 'Pending'),
        "inprogress": sum(1 for c in my_complaints if c['status'] == 'In Progress'),
        "resolved":   sum(1 for c in my_complaints if c['status'] == 'Resolved'),
    }
    return render_template('admin.html', complaints=my_complaints, stats=stats,
                           admin_category=admin_cat,
                           category_icon=CATEGORY_ICONS.get(admin_cat, '📋'),
                           category_icons=CATEGORY_ICONS)

@app.route('/update_status/<cid>', methods=['POST'])
def update_status(cid):
    if session.get('role') not in ('Admin', 'SuperAdmin'): return redirect(url_for('login_page'))
    new_status = request.form.get('status')
    response   = request.form.get('admin_response', '').strip()
    complaints_col.update_one(
        {"_id": ObjectId(cid)},
        {"$set": {"status": new_status, "admin_response": response,
                  "updated_at": datetime.datetime.now()}}
    )
    flash(f"Status updated to '{new_status}'.", "success")
    redirect_to = request.form.get('redirect_to', 'admin_dashboard')
    return redirect(url_for(redirect_to))

@app.route('/delete_complaint/<cid>', methods=['POST'])
def delete_complaint(cid):
    if session.get('role') not in ('Admin', 'SuperAdmin'): return redirect(url_for('login_page'))
    complaints_col.delete_one({"_id": ObjectId(cid)})
    flash("Complaint deleted.", "info")
    redirect_to = request.form.get('redirect_to', 'admin_dashboard')
    return redirect(url_for(redirect_to))

# ── Super Admin ──────────────────────────────────────────────────────
@app.route('/super_admin')
def super_admin():
    if session.get('role') != 'SuperAdmin': return redirect(url_for('login_page'))
    all_complaints = list(complaints_col.find().sort("created_at", -1))
    cat_stats = {}
    for cat in CATEGORIES:
        cc = [c for c in all_complaints if c.get('primary_category') == cat or c.get('secondary_category') == cat]
        cat_stats[cat] = {
            "total":    len(cc),
            "pending":  sum(1 for c in cc if c['status'] == 'Pending'),
            "resolved": sum(1 for c in cc if c['status'] == 'Resolved'),
            "icon":     CATEGORY_ICONS.get(cat, '📋'),
        }
    overall = {
        "total":      len(all_complaints),
        "pending":    sum(1 for c in all_complaints if c['status'] == 'Pending'),
        "inprogress": sum(1 for c in all_complaints if c['status'] == 'In Progress'),
        "resolved":   sum(1 for c in all_complaints if c['status'] == 'Resolved'),
        "users":      users_col.count_documents({"role": "Client"}),
    }
    admins = list(users_col.find({"role": "Admin"}))
    return render_template('super_admin.html',
                           complaints=all_complaints, cat_stats=cat_stats,
                           overall=overall, admins=admins,
                           categories=CATEGORIES, category_icons=CATEGORY_ICONS,
                           category_admins=CATEGORY_ADMINS)

if __name__ == '__main__':
    app.run(debug=True)