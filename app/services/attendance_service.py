from datetime import date, datetime, time, timedelta
from sqlalchemy import or_

from ..extensions import db
from ..models import Attendance, Holiday, ShiftAssignment


def active_shift_for(employee_id, on_date=None):
    on_date = on_date or date.today()
    assignment = (
        ShiftAssignment.query
        .filter(
            ShiftAssignment.employee_id == employee_id,
            ShiftAssignment.effective_from <= on_date,
            or_(ShiftAssignment.effective_to.is_(None), ShiftAssignment.effective_to >= on_date),
        )
        .order_by(ShiftAssignment.effective_from.desc())
        .first()
    )
    return assignment.shift if assignment else None


def check_in(employee, at=None, source="web"):
    at = at or datetime.now()
    today = at.date()
    if Holiday.query.filter_by(holiday_date=today).first():
        raise ValueError("Check-in is disabled on a configured holiday.")
    record = Attendance.query.filter_by(employee_id=employee.id, attendance_date=today).first()
    if record and record.check_in:
        raise ValueError("You have already checked in today.")
    if not record:
        record = Attendance(employee_id=employee.id, attendance_date=today, source=source)
        db.session.add(record)

    record.check_in = at
    shift = active_shift_for(employee.id, today)
    record.status = "present"
    record.late_minutes = 0
    if shift:
        scheduled = datetime.combine(today, shift.start_time)
        grace_end = scheduled + timedelta(minutes=shift.grace_minutes)
        if at > grace_end:
            record.late_minutes = int((at - scheduled).total_seconds() // 60)
            record.status = "late"
    return record


def check_out(employee, at=None):
    at = at or datetime.now()
    record = Attendance.query.filter_by(employee_id=employee.id, attendance_date=at.date()).first()
    if not record or not record.check_in:
        raise ValueError("Check in before checking out.")
    if record.check_out:
        raise ValueError("You have already checked out today.")
    if at <= record.check_in:
        raise ValueError("Check-out time must be after check-in time.")

    record.check_out = at
    shift = active_shift_for(employee.id, at.date())
    break_minutes = shift.break_minutes if shift else 0
    worked = max(0, int((at - record.check_in).total_seconds() // 60) - break_minutes)
    record.work_minutes = worked
    if shift:
        record.overtime_minutes = max(0, worked - shift.overtime_threshold_minutes)
        if worked < shift.minimum_half_day_minutes:
            record.status = "half_day"
    return record


def month_range(year, month):
    start = date(year, month, 1)
    next_month = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
    return start, next_month - timedelta(days=1)


def working_days(year, month):
    start, end = month_range(year, month)
    holidays = {h.holiday_date for h in Holiday.query.filter(Holiday.holiday_date.between(start, end)).all()}
    current = start
    count = 0
    while current <= end:
        if current.weekday() < 5 and current not in holidays:
            count += 1
        current += timedelta(days=1)
    return count
