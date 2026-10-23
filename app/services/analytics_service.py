from datetime import date, timedelta
from sqlalchemy import func
from ..extensions import db
from ..models import Attendance, Department, Employee, LeaveRequest, PayrollEntry, PayrollPeriod
from .attendance_service import month_range


def attendance_chart(year, month):
    start, end = month_range(year, month)
    rows = (
        db.session.query(Attendance.status, func.count(Attendance.id))
        .filter(Attendance.attendance_date.between(start, end))
        .group_by(Attendance.status)
        .all()
    )
    mapping = dict(rows)
    labels = ["Present", "Late", "Half day", "Absent", "Leave"]
    keys = ["present", "late", "half_day", "absent", "leave"]
    return {"labels": labels, "values": [mapping.get(k, 0) for k in keys]}


def department_headcount():
    rows = (
        db.session.query(Department.name, func.count(Employee.id))
        .outerjoin(Employee, db.and_(Employee.department_id == Department.id, Employee.status != "inactive"))
        .group_by(Department.id, Department.name)
        .order_by(Department.name)
        .all()
    )
    return {"labels": [r[0] for r in rows], "values": [r[1] for r in rows]}


def payroll_trend(limit=6):
    periods = PayrollPeriod.query.filter(PayrollPeriod.status != "draft").order_by(PayrollPeriod.year.desc(), PayrollPeriod.month.desc()).limit(limit).all()
    periods.reverse()
    labels, values = [], []
    for p in periods:
        total = db.session.query(func.coalesce(func.sum(PayrollEntry.net_pay), 0)).filter_by(period_id=p.id).scalar()
        labels.append(p.label)
        values.append(float(total or 0))
    return {"labels": labels, "values": values}
