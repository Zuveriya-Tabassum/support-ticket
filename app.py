from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for
from flask import send_file, make_response, request, session
from fpdf import FPDF
import io
from datetime import timedelta


db = SQLAlchemy()
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get("user")
        if not user or user.get("role") != "admin":
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

# ------------------- Load environment variables -------------------
load_dotenv()

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

app.secret_key = os.getenv("SECRET_KEY", "supersecret")

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------- Models -------------------

class User(db.Model):
    __tablename__ = 'users'
    active = db.Column(db.Boolean, default=True)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('user', 'admin', 'agent'), default='user')
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime)
    about = db.Column(db.Text)
    photo_url = db.Column(db.String(255))
    
    # Add the relationship!
    tickets = db.relationship(
    'Ticket',
    backref='owner',
    lazy='dynamic',
    foreign_keys='Ticket.user_id'  # This says: tickets where Ticket.user_id == User.id
    )



class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50))
    priority = db.Column(db.Enum('Low', 'Medium', 'High'), default='Low')
    status = db.Column(db.Enum('Open', 'In Progress', 'Resolved', 'Closed'), default='Open')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_agent = db.relationship(
        'User',
        primaryjoin='User.id == Ticket.assigned_to',
        foreign_keys=[assigned_to],
        uselist=False
    )

# Ticket.query.with_entities(Ticket.assigned_to).all()
    
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

with app.app_context():
    # results = Ticket.query.with_entities(Ticket.assigned_to).all()
    # print(results)
    db.create_all()

# ------------------- Routes -------------------

@app.route('/')
def home():
    return render_template("login.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

# ----------- ADMIN DASHBOARD ROUTES -----------

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    # Calculate admin stats
    total_tickets = Ticket.query.count()
    resolved_count = Ticket.query.filter_by(status='Resolved').count()
    pending_count = Ticket.query.filter(Ticket.status.in_(['Open', 'In Progress'])).count()
    urgent_count = Ticket.query.filter_by(priority='High').count()
    awaiting_assign = Ticket.query.filter_by(assigned_to=None).count()
    agents_count = User.query.filter_by(role='agent').count()
    admin = User.query.get(session["user"]["id"])
    return render_template(
        "admin_dashboard.html",
        admin=admin,
        total_tickets=total_tickets,
        resolved_count=resolved_count,
        pending_count=pending_count,
        urgent_count=urgent_count,
        awaiting_assign=awaiting_assign,
        agents_count=agents_count,
        pagename="dashboard"
    )


def build_summary_by_category(query):
    categories = db.session.query(Ticket.category).distinct().all()
    summary = []
    for cat_row in categories:
        cat = cat_row[0]
        qcat = query.filter_by(category=cat)
        open_count = qcat.filter_by(status="Open").count()
        closed_count = qcat.filter_by(status="Closed").count()
        resolved_count = qcat.filter_by(status="Resolved").count()
        resolved_cat = qcat.filter_by(status="Resolved").all()
        if resolved_cat:
            dt_cat = [
                (t.updated_at or t.created_at) - t.created_at
                for t in resolved_cat if t.updated_at and t.created_at
            ]
            avg_cat_seconds = sum([dt.total_seconds() for dt in dt_cat]) / len(dt_cat) if dt_cat else 0
            avg_cat_time = f"{round(avg_cat_seconds / 86400, 2)} days" if avg_cat_seconds else "-"
        else:
            avg_cat_time = "-"
        summary.append({
            "category": cat,
            "open": open_count,
            "closed": closed_count,
            "resolved": resolved_count,
            "avg_time": avg_cat_time
        })
    return summary

def generate_csv_data(summary_by_category):
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Category', 'Open', 'Closed', 'Resolved', 'Avg. Time to Resolve'])
    for row in summary_by_category:
        writer.writerow([row['category'], row['open'], row['closed'], row['resolved'], row['avg_time']])
    return output.getvalue()

@app.route('/admin/reports/download/<format>')
def download_report(format):
    # Parse filters, identical to /admin/reports
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status = request.args.get("status")
    agent_id = request.args.get("agent_id", type=int) if request.args.get("agent_id") else None

    query = Ticket.query
    if start_date:
        query = query.filter(Ticket.created_at >= start_date)
    if end_date:
        query = query.filter(Ticket.created_at <= end_date)
    if status:
        query = query.filter_by(status=status)
    if agent_id:
        query = query.filter_by(assigned_to=agent_id)

    summary_by_category = build_summary_by_category(query)

    # CSV
    if format == "csv":
        csv_data = generate_csv_data(summary_by_category)
        response = make_response(csv_data)
        response.headers['Content-Disposition'] = 'attachment; filename=report_export.csv'
        response.headers['Content-Type'] = 'text/csv'
        return response

    # XLSX
    elif format == "xlsx":
        import pandas as pd
        df = pd.DataFrame(summary_by_category)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name='report_export.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # PDF (correct in-memory streaming)
    elif format == "pdf":
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Support Ticket Report", ln=True)
        pdf.cell(200, 10, txt="Category | Open | Closed | Resolved | Avg. Time", ln=True)
        for row in summary_by_category:
            pdf.cell(200, 10, txt=f"{row['category']} | {row['open']} | {row['closed']} | {row['resolved']} | {row['avg_time']}", ln=True)
        pdf_bytes = pdf.output(dest="S").encode("latin1")
        output = io.BytesIO(pdf_bytes)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name='report_export.pdf', mimetype='application/pdf')

    return "Format not supported", 400

@app.route('/admin/tickets/assign', methods=['POST'])
@admin_required
def assign_ticket():
    data = request.json
    ticket_id = data['ticket_id']
    agent_id = data['agent_id']
    agent_user = User.query.filter_by(id=agent_id, role="agent").first()
    ticket = Ticket.query.get(ticket_id)
    if not ticket or not agent_user:
        return jsonify({"success": False, "message": "Invalid agent or ticket"})
    ticket.assigned_to = agent_user.id
    db.session.commit()
    return jsonify({"success": True})
# Example Flask/Python endpoint
@app.route('/deactivate/<int:item_id>', methods=['POST'])
def deactivate_item(item_id):
    item = Item.query.get(item_id)
    item.active = False
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/toggle_user_status/<int:user_id>', methods=['POST'])
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.active = not user.active
    db.session.commit()
    return jsonify({'success': True, 'active': user.active})

@app.route("/admin/tickets/<int:ticket_id>/details")
@admin_required
def ticket_details(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    user = User.query.get(ticket.user_id)
    comments = Comment.query.filter_by(ticket_id=ticket_id).all()
    return render_template("admin_ticket_details.html", ticket=ticket, user=user, comments=comments)


# Sidebar links
# from models import Ticket  # Import your Ticket model
# @app.route('/admin/tickets', methods=['GET'])
# def admin_all_tickets():
#     # Filtering
#     status = request.args.get('status')
#     priority = request.args.get('priority')
#     category = request.args.get('category')
    
#     # Get all users who are not agents (so, show 'user' and 'admin' tickets)
#     users = User.query.filter(User.role != 'agent').all()
    
#     # Apply filtering to each user's tickets
#     all_user_data = []
#     for user in users:
#         user_tickets = user.tickets
        
#         if status:
#             user_tickets = user_tickets.filter_by(status=status)
#         if priority:
#             user_tickets = user_tickets.filter_by(priority=priority)
#         if category:
#             user_tickets = user_tickets.filter(Ticket.category.ilike(f"%{category}%"))
            
#         user_tickets = user_tickets.order_by(Ticket.created_at.desc()).all()
#         all_user_data.append({"user": user, "tickets": user_tickets})

#     # Get the current admin (for sidebar, top bar)
#     admin = User.query.get(session.get('user', {}).get('id'))

# @app.route('/admin/tickets', methods=['GET'])
# def admin_all_tickets():
#     status = request.args.get('status')
#     priority = request.args.get('priority')
#     category = request.args.get('category')
#     users = User.query.filter(User.role != 'agent').all()  # or any subset you want

#     all_user_data = []
#     for user in users:
#         q = user.tickets
#         if status:
#             q = q.filter_by(status=status)
#         if priority:
#             q = q.filter_by(priority=priority)
#         if category:
#             q = q.filter(Ticket.category.ilike(f"%{category}%"))
#         tickets = q.order_by(Ticket.created_at.desc()).all()
#         all_user_data.append({'user': user, 'tickets': tickets})

#     admin = User.query.get(session['user']['id'])
#     # return render_template('admin_tickets.html', all_user_data=all_user_data, admin=admin)
#     return render_template("admin_tickets.html", all_user_data=all_user_data, admin=admin, pagename="tickets")  

@app.route('/admin/tickets', methods=['GET'])
def admin_all_tickets():
    status = request.args.get('status')
    priority = request.args.get('priority')
    category = request.args.get('category')

    # Only users who have tickets (exclude agents)
    users_with_tickets = (
        User.query
        .join(Ticket, User.id == Ticket.user_id)
        .filter(User.role != 'agent')
        .distinct()
        .all()
    )

    all_user_data = []
    ticket_ids = set()
    for user in users_with_tickets:
        q = user.tickets
        if status:
            q = q.filter_by(status=status)
        if priority:
            q = q.filter_by(priority=priority)
        if category:
            q = q.filter(Ticket.category.ilike(f"%{category}%"))
        tickets = q.order_by(Ticket.created_at.desc()).all()
        if tickets:
            all_user_data.append({'user': user, 'tickets': tickets})
            ticket_ids.update(t.id for t in tickets)

    # Gather all comments for tickets shown
    comments_map = {tid: [] for tid in ticket_ids}
    comments = Comment.query.filter(Comment.ticket_id.in_(ticket_ids)).order_by(Comment.created_at).all()
    for c in comments:
        comments_map[c.ticket_id].append(c)

    # Map user ids to names
    user_map = {u.id: u.name for u in User.query.all()}
    admin = User.query.get(session['user']['id'])

    return render_template(
        'admin_tickets.html',
        all_user_data=all_user_data,
        admin=admin,
        comments_map=comments_map,
        user_map=user_map
    )

def get_all_user_data(status=None, priority=None, category=None):
    # Query all users who are NOT agents and have tickets
    users_with_tickets = (
        User.query
        .join(Ticket, User.id == Ticket.user_id)
        .filter(User.role != 'agent')
        .distinct()
        .all()
    )

    all_user_data = []
    for user in users_with_tickets:
        q = user.tickets
        if status:
            q = q.filter_by(status=status)
        if priority:
            q = q.filter_by(priority=priority)
        if category:
            q = q.filter(Ticket.category.ilike(f"%{category}%"))
        tickets = q.order_by(Ticket.created_at.desc()).all()
        # Only display users if tickets remain after filters
        if tickets:
            all_user_data.append({'user': user, 'tickets': tickets})
    return all_user_data
@app.route('/admin_assign_tickets')
@admin_required
def admin_assign_tickets():
    status = request.args.get('status')
    priority = request.args.get('priority')
    category = request.args.get('category')
    agents = User.query.filter_by(role='agent').all()
    agent_map = {agent.id: agent.name for agent in agents}
    admin = User.query.get(session["user"]["id"])
    all_user_data = get_all_user_data(status, priority, category)
    agents = User.query.filter_by(role='agent').all()
    return render_template('admin_assign_tickets.html', admin=admin, all_user_data=all_user_data, agents=agents,agent_map=agent_map)

    


from collections import defaultdict
from datetime import datetime

@app.route("/admin/reports")
@admin_required
def admin_reports():
    # Filters
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status = request.args.get("status")
    agent_id = request.args.get("agent_id", type=int) if request.args.get("agent_id") else None

    agents = User.query.filter_by(role="agent").all()
    admin = User.query.get(session["user"]["id"])

    # Base query
    query = Ticket.query
    if start_date:
        query = query.filter(Ticket.created_at >= start_date)
    if end_date:
        query = query.filter(Ticket.created_at <= end_date)
    if status:
        query = query.filter_by(status=status)
    if agent_id:
        query = query.filter_by(assigned_to=agent_id)

    # KPIs (as above)
    total_tickets = query.count()
    resolved_count = query.filter_by(status='Resolved').count()
    pending_count = query.filter(Ticket.status.in_(['Open', 'In Progress'])).count()

    # Average resolution time (as above)
    resolved_tickets = query.filter_by(status='Resolved').all()
    if resolved_tickets:
        deltas = [
            (t.updated_at or t.created_at) - t.created_at
            for t in resolved_tickets if t.updated_at and t.created_at
        ]
        avg_seconds = sum([dt.total_seconds() for dt in deltas]) / len(deltas) if deltas else 0
        avg_res_time = f"{round(avg_seconds / 86400, 2)} days" if avg_seconds else "-"
    else:
        avg_res_time = "-"

    # --------- BAR/LINE CHART: TICKETS PER MONTH ----------
    # Find the last 6 months with tickets or all months in date filter
    ticket_list = query.all()
    month_counts = defaultdict(int)
    for t in ticket_list:
        if t.created_at:
            month_str = t.created_at.strftime("%b %Y")  # e.g., "Oct 2025"
            month_counts[month_str] += 1

    # If no tickets, fill with 0s for last 6 months
    if not month_counts:
        now = datetime.now()
        for i in range(6):
            month = (now.replace(day=1) - timedelta(days=30 * i)).strftime("%b %Y")
            month_counts[month] = 0
    months = sorted(month_counts, key=lambda x: datetime.strptime(x, "%b %Y"))
    bar_chart_data = [month_counts[m] for m in months]

    # --------- PIE CHART: TICKETS BY STATUS ----------
    statuses = ['Open', 'In Progress', 'Resolved', 'Closed']
    status_labels = statuses
    status_counts = [query.filter_by(status=s).count() for s in statuses]

    # --------- SUMMARY BY CATEGORY (as above) -----------
    categories = db.session.query(Ticket.category).distinct().all()
    summary_by_category = []
    for cat_row in categories:
        cat = cat_row[0]
        qcat = query.filter_by(category=cat)
        open_count = qcat.filter_by(status="Open").count()
        closed_count = qcat.filter_by(status="Closed").count()
        resolved_count_cat = qcat.filter_by(status="Resolved").count()
        resolved_cat = qcat.filter_by(status="Resolved").all()
        if resolved_cat:
            dt_cat = [
                (t.updated_at or t.created_at) - t.created_at
                for t in resolved_cat if t.updated_at and t.created_at
            ]
            avg_cat_seconds = sum([dt.total_seconds() for dt in dt_cat]) / len(dt_cat) if dt_cat else 0
            avg_cat_time = f"{round(avg_cat_seconds / 86400, 2)} days" if avg_cat_seconds else "-"
        else:
            avg_cat_time = "-"
        summary_by_category.append({
            "category": cat,
            "open": open_count,
            "closed": closed_count,
            "resolved": resolved_count_cat,
            "avg_time": avg_cat_time
        })

    return render_template(
        "admin_reports.html",
        agents=agents,
        admin=admin,
        start_date=start_date,
        end_date=end_date,
        total_tickets=total_tickets,
        resolved_count=resolved_count,
        pending_count=pending_count,
        avg_res_time=avg_res_time,
        summary_by_category=summary_by_category,
        months=months,
        bar_chart_data=bar_chart_data,
        status_labels=status_labels,
        status_counts=status_counts,
        pagename='reports',
        int=int
    )



@app.route("/admin_manage_users")
@admin_required
def admin_manage_users():
    # Get all users from the database
    users = User.query.all()
    # The currently logged-in admin info (for sidebar/profile)
    admin = User.query.get(session["user"]["id"])
    # Pass context variable for sidebar highlighting and page context
    return render_template(
        "admin_manage_users.html",
        users=users,
        admin=admin,
        pagename="users"
    )

@app.route("/admin/categories")
@admin_required
def admin_categories():
    # Implement category logic as needed
    return render_template("admin_categories.html", pagename="categories")

@app.route("/admin/settings")
@admin_required
def admin_settings():
    return render_template("admin_settings.html", pagename="settings")

@app.route("/admin/logs")
@admin_required
def admin_logs():
    # Implement logs if needed
    return render_template("admin_logs.html", pagename="logs")

@app.route("/admin/profile")
@admin_required
def admin_profile():
    admin = User.query.get(session["user"]["id"])
    return render_template("admin_profile.html", admin=admin, pagename="profile")

# ----------- SWITCH TO USER DASHBOARD -----------
@app.route("/user/dashboard")
def user_dashboard():
    # Only allow users/agents in this view
    user = session.get("user")
    if not user or user.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    u = User.query.get(user["id"])
    return render_template("user_dashboard.html", name=user["name"], profile_photo_url=u.photo_url, current_page="dashboard")

# ----------- GENERAL DASHBOARD SELECTOR -----------
# @app.route("/dashboard")
# def dashboard():
#     if "user" not in session:
#         return redirect(url_for("home"))
#     role = session["user"]["role"]
#     if role == "admin":
#         return redirect(url_for("admin_dashboard"))
#     elif role == "agent":
#         return render_template("agent_dashboard.html", name=session["user"]["name"], current_page="dashboard")
#     else:
#         user_id = session["user"]["id"]
#         user = User.query.get(user_id)
#         return render_template("user_dashboard.html", name=user.name, profile_photo_url=user.photo_url, current_page="dashboard")

@app.route("/tickets")
def tickets_page():
    return render_template("tickets.html")

@app.route("/assign-tickets")
def assign_tickets_page():
    return render_template("assign_tickets.html")

@app.route("/reports")
def reports_page():
    return render_template("reports.html")
@app.route("/userTickets")
def user_tickets_page():
    if "user" not in session:
        return redirect(url_for("login"))
    user_id = session["user"]["id"]
    user = User.query.get(user_id)
    tickets = Ticket.query.filter_by(user_id=user_id).order_by(Ticket.created_at.desc()).all()
    return render_template("userTickets.html", tickets=tickets,profile_photo_url=user.photo_url, current_page="tickets")

@app.route("/user_createdTickets", methods=["GET", "POST"])
def user_created_tickets_page():
    if "user" not in session:
        return redirect(url_for("login"))
    user_id = session["user"]["id"]              # Get user_id FIRST
    user = User.query.get(user_id)
    if request.method == "POST":
        category = request.form["category"]
        priority = request.form["priority"]
        description = request.form["description"]
        new_ticket = Ticket(
            user_id=user_id,
            category=category,
            priority=priority,
            description=description
        )
        db.session.add(new_ticket)
        db.session.commit()
        return redirect(url_for("user_tickets_page"))
    return render_template("user_createdTickets.html", profile_photo_url=user.photo_url, current_page="create_ticket")


@app.route("/userProfile", methods=["GET", "POST"])
def user_profile_page():
    if "user" not in session:
        return redirect(url_for("home"))

    user_id = session["user"]["id"]
    user = User.query.get(user_id)

    if request.method == "POST":
        # Get updated name and other fields
        new_name = request.form.get("name", user.name)
        user.name = new_name
        user.about = request.form.get("about", user.about)
        password = request.form.get("password")
        if password:
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        file = request.files.get("profile_photo")
        if file and file.filename != '':
            filename = f"profile_{user_id}.png"
            file.save(os.path.join("static/profile_images", filename))
            user.photo_url = f"/static/profile_images/{filename}"
        db.session.commit()

        # --- UPDATE SESSION so the dashboard gets the new name ---
        session["user"]["name"] = new_name

        return redirect(url_for("dashboard"))

    return render_template(
        "userProfile.html",
        name=user.name,
        email=user.email,
        about=getattr(user, "about", ""),
        profile_photo_url=getattr(user, "photo_url", None), current_page="profile"
    )

@app.route("/users")
def manage_users_page():
    return render_template("manage_users.html")

@app.route("/agents")
def manage_agents_page():
    return render_template("manage_agents.html")

@app.route("/my-tickets")
def my_tickets_page():
    if "user" in session:
        return render_template("my_tickets.html", name=session["user"]["name"])
    return redirect(url_for("home"))

@app.route("/agent")
def agent_page():
    return render_template("agent_dashboard.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))
    user_id = session["user"]["id"]
    user = User.query.get(user_id)
    role = session["user"]["role"]
    name = session["user"]["name"]
    if role == "admin":
        admin_user = User.query.get(user_id)
        return render_template("admin_dashboard.html", name=name, current_page="dashboard",admin=admin_user,
        total_tickets=Ticket.query.count(),
        resolved_count=Ticket.query.filter_by(status='Resolved').count(),
        pending_count=Ticket.query.filter(Ticket.status.in_(['Open','In Progress'])).count(),
        urgent_count=Ticket.query.filter_by(priority='High').count(),
        awaiting_assign=Ticket.query.filter_by(assigned_to=None).count(),
        agents_count=User.query.filter_by(role='agent').count(),
        pagename="dashboard")
    elif role == "agent":
        return render_template("agent_dashboard.html", name=name, current_page="dashboard")
    else:
        return render_template("user_dashboard.html", name=name,profile_photo_url=user.photo_url, current_page="dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ------------------- User APIs -------------------

@app.route('/users/signup', methods=['POST'])
def signup():
    data = request.json
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        role=data.get('role', 'user')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully", "user_id": new_user.id})

@app.route('/users/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    # Check if user exists and password is correct
    if user and bcrypt.check_password_hash(user.password, data['password']):
        if not user.active:
            return jsonify({"message": "Account is on hold. Please contact admin."}), 403
        session["user"] = {
            "id": user.id,
            "name": user.name,
            "role": user.role
        }
        user.last_login = datetime.now()
        db.session.commit()
        return jsonify({
            "message": "Login successful",
            "user_id": user.id,
            "role": user.role,
            "redirect": f"/dashboard"
        })
    return jsonify({"message": "Invalid email or password"}), 401

# ------------------- Ticket APIs -------------------

@app.route('/tickets', methods=['GET'])
def get_tickets():
    tickets = db.session.query(
        Ticket.id.label('ticket_id'),
        User.name.label('ticket_owner'),
        Ticket.category,
        Ticket.priority,
        Ticket.status,
        Ticket.description,
        Ticket.assigned_to
    ).join(User, Ticket.user_id == User.id).all()
    result = []
    for t in tickets:
        result.append({
            "ticket_id": t.ticket_id,
            "ticket_owner": t.ticket_owner,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "description": t.description,
            "assigned_to": t.assigned_to
        })
    return jsonify(result)

@app.route('/tickets', methods=['POST'])
@app.route('/tickets', methods=['POST'])
def create_ticket():
    # For a regular HTML form POST:
    user_id = session["user"]["id"]
    category = request.form["category"]
    priority = request.form["priority"]
    description = request.form["description"]
    new_ticket = Ticket(
        user_id=user_id,
        category=category,
        priority=priority,
        description=description
    )
    db.session.add(new_ticket)
    db.session.commit()
    return redirect(url_for("user_tickets_page"))

@app.route('/tickets/assigned/<int:agent_id>', methods=['GET'])
def assigned_tickets(agent_id):
    tickets = Ticket.query.filter_by(assigned_to=agent_id).all()
    return jsonify([{
        "id": t.id,
        "category": t.category,
        "priority": t.priority,
        "status": t.status,
        "description": t.description
    } for t in tickets])

@app.route('/tickets/filter', methods=['GET'])
def filter_tickets():
    status = request.args.get('status')
    priority = request.args.get('priority')
    query = Ticket.query
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    tickets = query.all()
    return jsonify([{
        "id": t.id,
        "category": t.category,
        "priority": t.priority,
        "status": t.status,
        "description": t.description
    } for t in tickets])

@app.route('/tickets/<int:ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    data = request.json
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({"message": "Ticket not found"}), 404
    ticket.status = data['status']
    db.session.commit()
    return jsonify({"message": f"Ticket status updated to {ticket.status}"})

# ------------------- Comment APIs -------------------

@app.route('/comments', methods=['POST'])
def add_comment():
    data = request.json
    new_comment = Comment(
        ticket_id=data['ticket_id'],
        user_id=data['user_id'],
        comment=data['comment']
    )
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({"message": "Comment added successfully", "comment_id": new_comment.id})

@app.route('/tickets/<int:ticket_id>/comments', methods=['GET'])
def get_comments(ticket_id):
    comments = Comment.query.filter_by(ticket_id=ticket_id).all()
    result = []
    for c in comments:
        user = User.query.get(c.user_id)
        result.append({
            "comment_id": c.id,
            "comment": c.comment,
            "commented_by": user.name if user else "Unknown",
            "created_at": c.created_at
        })
    return jsonify(result)

# ------------------- Analytics APIs -------------------
@app.route('/reports/ticket_counts', methods=['GET'])
def ticket_counts():
    counts = db.session.query(Ticket.status, db.func.count(Ticket.id)).group_by(Ticket.status).all()
    return jsonify({status: cnt for status, cnt in counts})

@app.route('/reports/agent_performance', methods=['GET'])
def agent_performance():
    agents = db.session.query(User).filter_by(role='agent').all()
    result = []
    for agent in agents:
        resolved = Ticket.query.filter_by(assigned_to=agent.id, status='Resolved').count()
        open_tickets = Ticket.query.filter_by(assigned_to=agent.id, status='Open').count()
        result.append({
            "agent": agent.name,
            "tickets_resolved": resolved,
            "open_tickets": open_tickets
        })
    return jsonify(result)

# ------------------- Run App -------------------
if __name__ == "__main__":
    app.run(debug=True)
