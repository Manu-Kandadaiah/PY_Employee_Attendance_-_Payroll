from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ...extensions import db
from ...forms import DepartmentForm, UserForm
from ...models import AuditLog, Department, Employee, User
from ...utils.audit import log_action
from ...utils.decorators import roles_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/")
@roles_required("admin")
def dashboard():
    counts = {
        "users": User.query.count(),
        "active_users": User.query.filter_by(is_active=True).count(),
        "employees": Employee.query.filter(Employee.status != "inactive").count(),
        "departments": Department.query.filter_by(is_active=True).count(),
    }
    role_rows = db.session.query(User.role, db.func.count(User.id)).group_by(User.role).all()
    role_chart = {"labels": [r[0].replace("_", " ").title() for r in role_rows], "values": [r[1] for r in role_rows]}
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(12).all()
    return render_template("admin/dashboard.html", counts=counts, role_chart=role_chart, recent_logs=recent_logs)


@admin_bp.route("/users", methods=["GET", "POST"])
@roles_required("admin")
def users():
    form = UserForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
        elif not form.password.data:
            form.password.errors.append("Password is required for a new user.")
        else:
            user = User(email=email, full_name=form.full_name.data.strip(), role=form.role.data, is_active=form.is_active.data)
            user.set_password(form.password.data)
            db.session.add(user)
            log_action("user_created", "user", None, {"email": email, "role": user.role})
            db.session.commit()
            flash("User created. Use HR > Employees for employment and payroll records.", "success")
            return redirect(url_for("admin.users"))
    query = User.query
    q = request.args.get("q", "").strip()
    if q:
        term = f"%{q}%"
        query = query.filter(db.or_(User.email.ilike(term), User.full_name.ilike(term)))
    items = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", form=form, users=items, q=q)


@admin_bp.post("/users/<int:user_id>/toggle")
@roles_required("admin")
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
    else:
        user.is_active = not user.is_active
        if user.employee_profile:
            user.employee_profile.status = "active" if user.is_active else "inactive"
        log_action("user_status_toggled", "user", user.id, {"is_active": user.is_active})
        db.session.commit()
        flash("User status updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.post("/users/<int:user_id>/role")
@roles_required("admin")
def update_role(user_id):
    user = User.query.get_or_404(user_id)
    role = request.form.get("role")
    if role not in {"admin", "hr", "manager", "employee"}:
        flash("Invalid role.", "danger")
    elif user.id == current_user.id and role != "admin":
        flash("You cannot remove your own administrator role.", "warning")
    else:
        old = user.role
        user.role = role
        log_action("user_role_changed", "user", user.id, {"from": old, "to": role})
        db.session.commit()
        flash("Role updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/departments", methods=["GET", "POST"])
@roles_required("admin")
def departments():
    form = DepartmentForm()
    if form.validate_on_submit():
        code = form.code.data.strip().upper()
        if Department.query.filter(db.or_(Department.name == form.name.data.strip(), Department.code == code)).first():
            flash("Department name or code already exists.", "danger")
        else:
            item = Department(name=form.name.data.strip(), code=code, description=form.description.data, is_active=form.is_active.data)
            db.session.add(item)
            log_action("department_created", "department", None, {"code": code})
            db.session.commit()
            flash("Department created.", "success")
            return redirect(url_for("admin.departments"))
    items = Department.query.order_by(Department.name).all()
    return render_template("admin/departments.html", form=form, departments=items)


@admin_bp.post("/departments/<int:department_id>/toggle")
@roles_required("admin")
def toggle_department(department_id):
    item = Department.query.get_or_404(department_id)
    item.is_active = not item.is_active
    log_action("department_status_toggled", "department", item.id, {"is_active": item.is_active})
    db.session.commit()
    flash("Department status updated.", "success")
    return redirect(url_for("admin.departments"))


@admin_bp.get("/audit-logs")
@roles_required("admin")
def audit_logs():
    page = request.args.get("page", 1, type=int)
    action = request.args.get("action", "").strip()
    query = AuditLog.query
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    pagination = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template("admin/audit_logs.html", pagination=pagination, action=action)
