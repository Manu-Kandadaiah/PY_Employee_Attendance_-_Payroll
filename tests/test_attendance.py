from datetime import datetime, date

from app.extensions import db
from app.models import Attendance, Employee
from app.services.attendance_service import check_in, check_out


def test_checkin_checkout_calculates_time(app):
    with app.app_context():
        employee = Employee.query.filter_by(employee_code="E003").first()
        check_in(employee, datetime(2026, 7, 9, 9, 25))
        db.session.commit()
        record = check_out(employee, datetime(2026, 7, 9, 19, 0))
        db.session.commit()
        assert record.status == "late"
        assert record.late_minutes == 25
        assert record.work_minutes == 515
        assert record.overtime_minutes == 35


def test_duplicate_checkin_rejected(app):
    with app.app_context():
        employee = Employee.query.filter_by(employee_code="E003").first()
        check_in(employee, datetime(2026, 7, 8, 9, 0))
        db.session.commit()
        try:
            check_in(employee, datetime(2026, 7, 8, 9, 5))
            assert False, "duplicate check-in should fail"
        except ValueError:
            pass
