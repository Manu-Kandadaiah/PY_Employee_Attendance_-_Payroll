from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from ..extensions import db
from ..models import (
    Attendance, Employee, LeaveRequest, OvertimeRequest, PayrollEntry,
    PayrollLineItem, SalaryStructure,
)
from .attendance_service import month_range, working_days

MONEY = Decimal("0.01")


def D(value):
    return Decimal(str(value or 0))


def money(value):
    return D(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def current_salary(employee_id, period_end):
    return (
        SalaryStructure.query
        .filter(
            SalaryStructure.employee_id == employee_id,
            SalaryStructure.is_active.is_(True),
            SalaryStructure.effective_from <= period_end,
        )
        .order_by(SalaryStructure.effective_from.desc())
        .first()
    )


def calculate_employee_payroll(employee, period):
    start, end = month_range(period.year, period.month)
    salary = current_salary(employee.id, end)
    if not salary:
        return None

    total_working_days = period.working_days or working_days(period.year, period.month)
    records = Attendance.query.filter(
        Attendance.employee_id == employee.id,
        Attendance.attendance_date.between(start, end),
    ).all()
    attendance_days = sum(Decimal("0.5") if r.status == "half_day" else Decimal("1") for r in records if r.status in {"present", "late", "half_day"})

    approved_leaves = LeaveRequest.query.filter(
        LeaveRequest.employee_id == employee.id,
        LeaveRequest.status == "approved",
        LeaveRequest.start_date <= end,
        LeaveRequest.end_date >= start,
    ).all()
    paid_leave_days = sum(D(l.days) for l in approved_leaves if l.leave_type.is_paid)
    unpaid_leave_days = sum(D(l.days) for l in approved_leaves if not l.leave_type.is_paid)
    payable_days = min(D(total_working_days), attendance_days + paid_leave_days)
    absent_days = max(Decimal("0"), D(total_working_days) - payable_days - unpaid_leave_days)
    unpaid_days = unpaid_leave_days + absent_days
    factor = payable_days / D(total_working_days) if total_working_days else Decimal("0")

    overtime_minutes = db.session.query(db.func.coalesce(db.func.sum(OvertimeRequest.approved_minutes), 0)).filter(
        OvertimeRequest.employee_id == employee.id,
        OvertimeRequest.status == "approved",
        OvertimeRequest.attendance_id == Attendance.id,
        Attendance.attendance_date.between(start, end),
    ).scalar() or 0
    overtime_hours = D(overtime_minutes) / Decimal("60")

    basic = money(D(salary.basic) * factor)
    hra = money(D(salary.hra) * factor)
    allowances = money((D(salary.conveyance) + D(salary.medical) + D(salary.special_allowance) + D(salary.variable_pay)) * factor)
    hourly_basic = D(salary.basic) / D(total_working_days * 8) if total_working_days else Decimal("0")
    overtime_pay = money(overtime_hours * hourly_basic * D(salary.overtime_multiplier))
    gross = money(basic + hra + allowances + overtime_pay)

    pf = money(basic * D(salary.pf_percent) / Decimal("100"))
    professional_tax = money(salary.professional_tax)
    income_tax = money(gross * D(salary.income_tax_percent) / Decimal("100"))
    other = money(salary.other_deduction)
    deductions = money(pf + professional_tax + income_tax + other)
    net = money(max(Decimal("0"), gross - deductions))

    entry = PayrollEntry.query.filter_by(period_id=period.id, employee_id=employee.id).first()
    if not entry:
        entry = PayrollEntry(period_id=period.id, employee_id=employee.id)
        db.session.add(entry)
    entry.attendance_days = attendance_days
    entry.paid_leave_days = paid_leave_days
    entry.unpaid_leave_days = unpaid_days
    entry.overtime_hours = overtime_hours
    entry.basic = basic
    entry.hra = hra
    entry.allowances = allowances
    entry.overtime_pay = overtime_pay
    entry.gross_pay = gross
    entry.pf_deduction = pf
    entry.professional_tax = professional_tax
    entry.income_tax = income_tax
    entry.other_deductions = other
    entry.total_deductions = deductions
    entry.net_pay = net

    entry.line_items.clear()
    items = [
        ("earning", "BASIC", "Basic salary", basic),
        ("earning", "HRA", "House rent allowance", hra),
        ("earning", "ALLOW", "Other allowances", allowances),
        ("earning", "OT", "Approved overtime", overtime_pay),
        ("deduction", "PF", "Provident fund", pf),
        ("deduction", "PT", "Professional tax", professional_tax),
        ("deduction", "TDS", "Income tax / TDS", income_tax),
        ("deduction", "OTHER", "Other deductions", other),
    ]
    for category, code, description, amount in items:
        if amount:
            entry.line_items.append(PayrollLineItem(category=category, code=code, description=description, amount=amount))
    return entry


def generate_period(period):
    period.working_days = working_days(period.year, period.month)
    active_employees = Employee.query.filter(Employee.status.in_(["active", "probation", "notice"])).all()
    generated = 0
    skipped = []
    for employee in active_employees:
        entry = calculate_employee_payroll(employee, period)
        if entry:
            generated += 1
        else:
            skipped.append(employee.employee_code)
    return generated, skipped
