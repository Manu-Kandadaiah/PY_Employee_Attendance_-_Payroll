from datetime import date
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ...extensions import db
from ...forms import ShiftAssignmentForm
from ...models import Attendance, Employee, LeaveBalance, LeaveRequest, OvertimeRequest, Shift, ShiftAssignment
from ...models.mixins import utcnow
from ...services.attendance_service import month_range
from ...services.notification_service import notify_user
from ...utils.audit import log_action
from ...utils.decorators import roles_required

manager_bp = Blueprint("manager", __name__)


def team_base_query():
    query = Employee.query.filter(Employee.status != "inactive")
    if current_user.role == "manager":
        profile = current_user.employee_profile
        if not profile:
            return query.filter(db.false())
        query = query.filter(Employee.manager_id == profile.id)
    return query


@manager_bp.get("/")
@roles_required("manager", "hr", "admin")
def dashboard():
    today = date.today()
    team = team_base_query().all()
    ids = [e.id for e in team]
    present = Attendance.query.filter(Attendance.employee_id.in_(ids), Attendance.attendance_date == today, Attendance.status.in_(["present", "late", "half_day"])).count() if ids else 0
    pending_leaves = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(ids), LeaveRequest.status == "pending").count() if ids else 0
    pending_ot = OvertimeRequest.query.filter(OvertimeRequest.employee_id.in_(ids), OvertimeRequest.status == "pending").count() if ids else 0
    start, end = month_range(today.year, today.month)
    late_count = Attendance.query.filter(Attendance.employee_id.in_(ids), Attendance.attendance_date.between(start, end), Attendance.status == "late").count() if ids else 0
    department_counts = {}
    for employee in team:
        department_counts[employee.department.name] = department_counts.get(employee.department.name, 0) + 1
    chart = {"labels": list(department_counts.keys()), "values": list(department_counts.values())}
    recent_leaves = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(ids)).order_by(LeaveRequest.created_at.desc()).limit(8).all() if ids else []
    return render_template("manager/dashboard.html", team_count=len(team), present=present, pending_leaves=pending_leaves, pending_ot=pending_ot, late_count=late_count, chart=chart, recent_leaves=recent_leaves)


@manager_bp.get("/team")
@roles_required("manager", "hr", "admin")
def team():
    employees = team_base_query().order_by(Employee.employee_code).all()
    return render_template("manager/team.html", employees=employees)


@manager_bp.get("/attendance")
@roles_required("manager", "hr", "admin")
def attendance():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)
    start, end = month_range(year, month)
    ids = [e.id for e in team_base_query().all()]
    records = Attendance.query.filter(Attendance.employee_id.in_(ids), Attendance.attendance_date.between(start, end)).order_by(Attendance.attendance_date.desc()).all() if ids else []
    return render_template("manager/attendance.html", records=records, year=year, month=month)


@manager_bp.get("/leaves")
@roles_required("manager", "hr", "admin")
def leaves():
    ids = [e.id for e in team_base_query().all()]
    status = request.args.get("status", "pending")
    query = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(ids)) if ids else LeaveRequest.query.filter(db.false())
    if status != "all":
        query = query.filter_by(status=status)
    items = query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template("manager/leaves.html", items=items, status=status)


@manager_bp.post("/leaves/<int:request_id>/<decision>")
@roles_required("manager", "hr", "admin")
def review_leave(request_id, decision):
    if decision not in {"approve", "reject"}:
        return ("Invalid decision", 400)
    ids = [e.id for e in team_base_query().all()]
    item = LeaveRequest.query.filter(LeaveRequest.id == request_id, LeaveRequest.employee_id.in_(ids), LeaveRequest.status == "pending").first_or_404()
    comments = request.form.get("comments", "")[:255]
    item.status = "approved" if decision == "approve" else "rejected"
    item.approved_by_user_id = current_user.id
    item.reviewed_at = utcnow()
    item.reviewer_comments = comments
    balance = LeaveBalance.query.filter_by(employee_id=item.employee_id, leave_type_id=item.leave_type_id, year=item.start_date.year).first()
    if balance:
        balance.pending_days = max(0, float(balance.pending_days) - float(item.days))
        if decision == "approve":
            balance.used_days = float(balance.used_days) + float(item.days)
    notify_user(item.employee.user_id, f"Leave request {item.status}", f"Your {item.leave_type.name} request for {item.start_date:%d %b}–{item.end_date:%d %b %Y} was {item.status}.", "success" if decision == "approve" else "danger", url_for("employee.leaves"))
    log_action(f"leave_{item.status}", "leave_request", item.id, {"comments": comments})
    db.session.commit()
    flash(f"Leave request {item.status}.", "success")
    return redirect(url_for("manager.leaves"))


@manager_bp.get("/overtime")
@roles_required("manager", "hr", "admin")
def overtime():
    ids = [e.id for e in team_base_query().all()]
    status = request.args.get("status", "pending")
    query = OvertimeRequest.query.filter(OvertimeRequest.employee_id.in_(ids)) if ids else OvertimeRequest.query.filter(db.false())
    if status != "all":
        query = query.filter_by(status=status)
    items = query.order_by(OvertimeRequest.created_at.desc()).all()
    return render_template("manager/overtime.html", items=items, status=status)


@manager_bp.post("/overtime/<int:request_id>/<decision>")
@roles_required("manager", "hr", "admin")
def review_overtime(request_id, decision):
    if decision not in {"approve", "reject"}:
        return ("Invalid decision", 400)
    ids = [e.id for e in team_base_query().all()]
    item = OvertimeRequest.query.filter(OvertimeRequest.id == request_id, OvertimeRequest.employee_id.in_(ids), OvertimeRequest.status == "pending").first_or_404()
    approved = request.form.get("approved_minutes", type=int)
    item.status = "approved" if decision == "approve" else "rejected"
    item.approved_minutes = min(max(approved if approved is not None else item.requested_minutes, 0), item.requested_minutes) if decision == "approve" else 0
    item.reviewed_by_user_id = current_user.id
    item.reviewer_comments = request.form.get("comments", "")[:255]
    notify_user(item.employee.user_id, f"Overtime request {item.status}", f"Overtime for {item.attendance.attendance_date:%d %b %Y} was {item.status}. Approved: {item.approved_minutes / 60:.1f} hours.", "success" if decision == "approve" else "danger", url_for("employee.attendance"))
    log_action(f"overtime_{item.status}", "overtime_request", item.id)
    db.session.commit()
    flash(f"Overtime request {item.status}.", "success")
    return redirect(url_for("manager.overtime"))


@manager_bp.route("/shifts", methods=["GET", "POST"])
@roles_required("manager", "hr", "admin")
def shifts():
    form = ShiftAssignmentForm()
    employees = team_base_query().order_by(Employee.employee_code).all()
    form.employee_id.choices = [(e.id, f"{e.employee_code} — {e.display_name}") for e in employees]
    form.shift_id.choices = [(s.id, f"{s.name} ({s.code})") for s in Shift.query.filter_by(is_active=True).order_by(Shift.name).all()]
    if form.validate_on_submit():
        if form.employee_id.data not in {e.id for e in employees}:
            flash("Employee is outside your reporting scope.", "danger")
        else:
            assignment = ShiftAssignment(employee_id=form.employee_id.data, shift_id=form.shift_id.data, effective_from=form.effective_from.data, effective_to=form.effective_to.data)
            db.session.add(assignment)
            log_action("shift_assigned", "employee", form.employee_id.data, {"shift_id": form.shift_id.data})
            db.session.commit()
            flash("Shift assigned.", "success")
            return redirect(url_for("manager.shifts"))
    ids = [e.id for e in employees]
    assignments = ShiftAssignment.query.filter(ShiftAssignment.employee_id.in_(ids)).order_by(ShiftAssignment.effective_from.desc()).limit(100).all() if ids else []
    return render_template("manager/shifts.html", form=form, assignments=assignments)
