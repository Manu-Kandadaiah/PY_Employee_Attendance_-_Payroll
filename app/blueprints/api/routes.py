from datetime import date
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from ...extensions import db
from ...models import Attendance, Employee, Holiday, LeaveRequest, Notification, PayrollEntry
from ...services.attendance_service import check_in, check_out, month_range
from ...utils.audit import log_action
from ...utils.decorators import roles_required

api_bp = Blueprint("api", __name__)


def attendance_json(record):
    return {
        "id": record.id,
        "date": record.attendance_date.isoformat(),
        "check_in": record.check_in.isoformat() if record.check_in else None,
        "check_out": record.check_out.isoformat() if record.check_out else None,
        "status": record.status,
        "work_minutes": record.work_minutes,
        "late_minutes": record.late_minutes,
        "overtime_minutes": record.overtime_minutes,
    }


@api_bp.get("/me")
@login_required
def me():
    employee = current_user.employee_profile
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "employee": None if not employee else {
            "id": employee.id,
            "employee_code": employee.employee_code,
            "designation": employee.designation,
            "department": employee.department.name,
        },
    })


@api_bp.get("/attendance")
@roles_required("employee", "manager", "hr")
def attendance_list():
    employee = current_user.employee_profile
    if not employee:
        return jsonify({"error": "Employee profile not found"}), 404
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)
    start, end = month_range(year, month)
    records = Attendance.query.filter(Attendance.employee_id == employee.id, Attendance.attendance_date.between(start, end)).order_by(Attendance.attendance_date).all()
    return jsonify({"data": [attendance_json(r) for r in records]})


@api_bp.post("/attendance/check-in")
@roles_required("employee", "manager", "hr")
def api_check_in():
    employee = current_user.employee_profile
    if not employee:
        return jsonify({"error": "Employee profile not found"}), 404
    try:
        record = check_in(employee, source="web")
        log_action("api_attendance_check_in", "attendance", record.id)
        db.session.commit()
        return jsonify({"data": attendance_json(record)}), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 409


@api_bp.post("/attendance/check-out")
@roles_required("employee", "manager", "hr")
def api_check_out():
    employee = current_user.employee_profile
    if not employee:
        return jsonify({"error": "Employee profile not found"}), 404
    try:
        record = check_out(employee)
        log_action("api_attendance_check_out", "attendance", record.id)
        db.session.commit()
        return jsonify({"data": attendance_json(record)})
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 409


@api_bp.get("/holidays")
@login_required
def holidays():
    year = request.args.get("year", date.today().year, type=int)
    items = Holiday.query.filter(db.extract("year", Holiday.holiday_date) == year).order_by(Holiday.holiday_date).all()
    return jsonify({"data": [{"date": h.holiday_date.isoformat(), "name": h.name, "optional": h.is_optional} for h in items]})


@api_bp.get("/notifications")
@login_required
def notifications():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify({"data": [{"id": n.id, "title": n.title, "message": n.message, "category": n.category, "is_read": n.is_read, "created_at": n.created_at.isoformat()} for n in items]})


@api_bp.get("/employees")
@roles_required("hr", "admin")
def employees():
    items = Employee.query.filter(Employee.status != "inactive").order_by(Employee.employee_code).all()
    return jsonify({"data": [{"id": e.id, "employee_code": e.employee_code, "name": e.display_name, "email": e.user.email, "department": e.department.name, "designation": e.designation, "status": e.status} for e in items]})


@api_bp.get("/payroll/<int:entry_id>")
@login_required
def payroll_entry(entry_id):
    entry = PayrollEntry.query.get_or_404(entry_id)
    if current_user.role not in {"hr", "admin"} and (not current_user.employee_profile or entry.employee_id != current_user.employee_profile.id):
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({"data": {
        "period": entry.period.label,
        "employee_code": entry.employee.employee_code,
        "gross_pay": float(entry.gross_pay),
        "total_deductions": float(entry.total_deductions),
        "net_pay": float(entry.net_pay),
        "payment_status": entry.payment_status,
        "line_items": [{"category": i.category, "code": i.code, "description": i.description, "amount": float(i.amount)} for i in entry.line_items],
    }})
