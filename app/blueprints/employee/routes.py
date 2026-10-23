from datetime import date, datetime, timedelta
from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user

from ...extensions import db
from ...forms import EmployeeProfileForm, LeaveRequestForm, OvertimeRequestForm
from ...models import Attendance, Holiday, LeaveBalance, LeaveRequest, LeaveType, Notification, OvertimeRequest, PayrollEntry
from ...models.mixins import utcnow
from ...services.attendance_service import check_in, check_out, month_range
from ...services.notification_service import notify_roles
from ...services.pdf_service import build_payslip_pdf
from ...utils.audit import log_action
from ...utils.decorators import roles_required

employee_bp = Blueprint("employee", __name__)


def employee_or_404():
    from flask import abort
    employee = current_user.employee_profile
    if not employee:
        abort(404)
    return employee


@employee_bp.get("/")
@roles_required("employee", "manager", "hr")
def dashboard():
    employee = employee_or_404()
    today = date.today()
    today_record = Attendance.query.filter_by(employee_id=employee.id, attendance_date=today).first()
    start, end = month_range(today.year, today.month)
    records = Attendance.query.filter(Attendance.employee_id == employee.id, Attendance.attendance_date.between(start, end)).order_by(Attendance.attendance_date.desc()).all()
    present_days = sum(1 for r in records if r.status in {"present", "late", "half_day"})
    overtime_hours = sum(r.overtime_minutes for r in records) / 60
    leave_balances = LeaveBalance.query.filter_by(employee_id=employee.id, year=today.year).all()
    latest_payslip = PayrollEntry.query.filter_by(employee_id=employee.id).join(PayrollEntry.period).order_by(db.desc("year"), db.desc("month")).first()
    upcoming_holidays = Holiday.query.filter(Holiday.holiday_date >= today).order_by(Holiday.holiday_date).limit(5).all()
    chart = {
        "labels": [r.attendance_date.strftime("%d %b") for r in reversed(records[:10])],
        "values": [round(r.work_minutes / 60, 1) for r in reversed(records[:10])],
    }
    return render_template("employee/dashboard.html", employee=employee, today_record=today_record, present_days=present_days, overtime_hours=overtime_hours, leave_balances=leave_balances, latest_payslip=latest_payslip, upcoming_holidays=upcoming_holidays, chart=chart)


@employee_bp.route("/profile", methods=["GET", "POST"])
@roles_required("employee", "manager", "hr")
def profile():
    employee = employee_or_404()
    form = EmployeeProfileForm(obj=employee)
    if form.validate_on_submit():
        form.populate_obj(employee)
        for attr in ("pan_number", "bank_ifsc"):
            value = getattr(employee, attr)
            if value:
                setattr(employee, attr, value.upper().strip())
        log_action("profile_updated", "employee", employee.id)
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("employee.profile"))
    return render_template("employee/profile.html", form=form, employee=employee)


@employee_bp.get("/attendance")
@roles_required("employee", "manager", "hr")
def attendance():
    employee = employee_or_404()
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)
    start, end = month_range(year, month)
    records = Attendance.query.filter(Attendance.employee_id == employee.id, Attendance.attendance_date.between(start, end)).order_by(Attendance.attendance_date.desc()).all()
    return render_template("employee/attendance.html", records=records, year=year, month=month, today=today)


@employee_bp.post("/attendance/check-in")
@roles_required("employee", "manager", "hr")
def attendance_check_in():
    employee = employee_or_404()
    try:
        record = check_in(employee)
        log_action("attendance_check_in", "attendance", record.id, {"time": record.check_in})
        db.session.commit()
        flash("Check-in recorded.", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "warning")
    return redirect(request.referrer or url_for("employee.dashboard"))


@employee_bp.post("/attendance/check-out")
@roles_required("employee", "manager", "hr")
def attendance_check_out():
    employee = employee_or_404()
    try:
        record = check_out(employee)
        log_action("attendance_check_out", "attendance", record.id, {"time": record.check_out, "work_minutes": record.work_minutes})
        db.session.commit()
        flash("Check-out recorded.", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "warning")
    return redirect(request.referrer or url_for("employee.dashboard"))


@employee_bp.route("/overtime/<int:attendance_id>/request", methods=["GET", "POST"])
@roles_required("employee", "manager", "hr")
def request_overtime(attendance_id):
    employee = employee_or_404()
    record = Attendance.query.filter_by(id=attendance_id, employee_id=employee.id).first_or_404()
    if record.overtime_minutes <= 0:
        flash("This attendance record has no calculated overtime.", "warning")
        return redirect(url_for("employee.attendance"))
    if record.overtime_request:
        flash("An overtime request already exists for this date.", "warning")
        return redirect(url_for("employee.attendance"))
    form = OvertimeRequestForm()
    if form.validate_on_submit():
        item = OvertimeRequest(employee_id=employee.id, attendance_id=record.id, requested_minutes=record.overtime_minutes, reason=form.reason.data)
        db.session.add(item)
        notify_roles(["manager", "hr", "admin"], "Overtime approval required", f"{employee.display_name} submitted {record.overtime_minutes / 60:.1f} overtime hours.", "warning", url_for("manager.overtime"))
        log_action("overtime_requested", "attendance", record.id)
        db.session.commit()
        flash("Overtime approval requested.", "success")
        return redirect(url_for("employee.attendance"))
    return render_template("employee/overtime_form.html", form=form, record=record)


def business_days(start_date, end_date):
    holidays = {h.holiday_date for h in Holiday.query.filter(Holiday.holiday_date.between(start_date, end_date)).all()}
    current, count = start_date, 0
    while current <= end_date:
        if current.weekday() < 5 and current not in holidays:
            count += 1
        current += timedelta(days=1)
    return count


@employee_bp.route("/leaves", methods=["GET", "POST"])
@roles_required("employee", "manager", "hr")
def leaves():
    employee = employee_or_404()
    form = LeaveRequestForm()
    form.leave_type_id.choices = [(x.id, f"{x.name} ({x.code})") for x in LeaveType.query.filter_by(is_active=True).order_by(LeaveType.name).all()]
    if form.validate_on_submit():
        days = business_days(form.start_date.data, form.end_date.data)
        if days <= 0:
            flash("The selected range has no working days.", "warning")
        else:
            balance = LeaveBalance.query.filter_by(employee_id=employee.id, leave_type_id=form.leave_type_id.data, year=form.start_date.data.year).first()
            leave_type = db.session.get(LeaveType, form.leave_type_id.data)
            if balance and leave_type.is_paid and balance.available_days < days:
                flash(f"Insufficient balance. Available: {balance.available_days:g} days.", "danger")
            else:
                item = LeaveRequest(employee_id=employee.id, leave_type_id=form.leave_type_id.data, start_date=form.start_date.data, end_date=form.end_date.data, days=days, reason=form.reason.data)
                if balance:
                    balance.pending_days = float(balance.pending_days) + days
                db.session.add(item)
                notify_roles(["manager", "hr", "admin"], "Leave approval required", f"{employee.display_name} requested {days} day(s) of {leave_type.name}.", "warning", url_for("manager.leaves"))
                log_action("leave_requested", "leave_request", None, {"days": days})
                db.session.commit()
                flash("Leave request submitted.", "success")
                return redirect(url_for("employee.leaves"))
    requests = LeaveRequest.query.filter_by(employee_id=employee.id).order_by(LeaveRequest.created_at.desc()).all()
    balances = LeaveBalance.query.filter_by(employee_id=employee.id, year=date.today().year).all()
    return render_template("employee/leaves.html", form=form, requests=requests, balances=balances)


@employee_bp.post("/leaves/<int:request_id>/cancel")
@roles_required("employee", "manager", "hr")
def cancel_leave(request_id):
    employee = employee_or_404()
    item = LeaveRequest.query.filter_by(id=request_id, employee_id=employee.id, status="pending").first_or_404()
    balance = LeaveBalance.query.filter_by(employee_id=employee.id, leave_type_id=item.leave_type_id, year=item.start_date.year).first()
    if balance:
        balance.pending_days = max(0, float(balance.pending_days) - float(item.days))
    item.status = "cancelled"
    log_action("leave_cancelled", "leave_request", item.id)
    db.session.commit()
    flash("Leave request cancelled.", "success")
    return redirect(url_for("employee.leaves"))


@employee_bp.get("/payslips")
@roles_required("employee", "manager", "hr")
def payslips():
    employee = employee_or_404()
    entries = PayrollEntry.query.filter_by(employee_id=employee.id).join(PayrollEntry.period).order_by(db.desc("year"), db.desc("month")).all()
    return render_template("employee/payslips.html", entries=entries)


@employee_bp.get("/payslips/<int:entry_id>.pdf")
@roles_required("employee", "manager", "hr")
def download_payslip(entry_id):
    employee = employee_or_404()
    entry = PayrollEntry.query.filter_by(id=entry_id, employee_id=employee.id).first_or_404()
    pdf = build_payslip_pdf(entry, current_app.config["COMPANY_NAME"], current_app.config["COMPANY_ADDRESS"])
    log_action("payslip_downloaded", "payroll_entry", entry.id)
    db.session.commit()
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name=f"payslip-{employee.employee_code}-{entry.period.year}-{entry.period.month:02d}.pdf")


@employee_bp.get("/notifications")
@roles_required("employee", "manager", "hr")
def notifications():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return render_template("shared/notifications.html", items=items)


@employee_bp.post("/notifications/<int:notification_id>/read")
@roles_required("employee", "manager", "hr")
def mark_notification_read(notification_id):
    item = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    item.is_read = True
    db.session.commit()
    return redirect(item.link or url_for("employee.notifications"))
