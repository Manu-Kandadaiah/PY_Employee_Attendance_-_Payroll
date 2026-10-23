from datetime import date, datetime, time, timedelta

from app.extensions import db
from app.models import Attendance, Employee, PayrollPeriod
from app.services.attendance_service import working_days
from app.services.payroll_service import generate_period
from app.services.pdf_service import build_payslip_pdf


def test_payroll_generation_and_pdf(app):
    with app.app_context():
        employee = Employee.query.filter_by(employee_code="E003").first()
        year, month = 2026, 6
        current = date(year, month, 1)
        end = date(year, month, 30)
        while current <= end:
            if current.weekday() < 5:
                db.session.add(Attendance(employee=employee, attendance_date=current, check_in=datetime.combine(current,time(9)), check_out=datetime.combine(current,time(18)), status="present", work_minutes=480))
            current += timedelta(days=1)
        period = PayrollPeriod(year=year, month=month, working_days=working_days(year, month))
        db.session.add(period)
        db.session.flush()
        generated, skipped = generate_period(period)
        db.session.commit()
        assert generated == 3
        assert skipped == []
        entry = period.entries.filter_by(employee_id=employee.id).first()
        assert float(entry.gross_pay) > 0
        assert float(entry.net_pay) < float(entry.gross_pay)
        pdf = build_payslip_pdf(entry, "Test Company", "Bengaluru")
        assert pdf.read(4) == b"%PDF"
