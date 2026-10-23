import csv
from datetime import date, datetime, timedelta
from io import StringIO
from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user

from ...extensions import db
from ...forms import EmployeeForm, HolidayForm, LeaveTypeForm, PayrollPeriodForm, ShiftForm
from ...models import (
    Attendance, Department, Employee, Holiday, LeaveBalance, LeaveRequest, LeaveType,
    PayrollEntry, PayrollPeriod, SalaryStructure, Shift, User,
)
from ...models.mixins import utcnow
from ...services.analytics_service import attendance_chart, department_headcount, payroll_trend
from ...services.attendance_service import month_range
from ...services.notification_service import notify_user
from ...services.payroll_service import generate_period
from ...services.pdf_service import build_payslip_pdf
from ...utils.audit import log_action
from ...utils.decorators import roles_required

hr_bp = Blueprint("hr", __name__)


def employee_choices():
    return [(0, "No reporting manager")] + [(e.id, f"{e.employee_code} — {e.display_name}") for e in Employee.query.filter(Employee.status != "inactive").order_by(Employee.employee_code).all()]


def configure_employee_form(form):
    form.department_id.choices = [(d.id, f"{d.code} — {d.name}") for d in Department.query.filter_by(is_active=True).order_by(Department.name).all()]
    form.manager_id.choices = employee_choices()


def salary_from_form(employee, form, new=False):
    salary = employee.salary_structures.filter_by(is_active=True).order_by(SalaryStructure.effective_from.desc()).first()
    if not salary:
        salary = SalaryStructure(employee=employee, effective_from=form.date_of_joining.data or date.today())
        db.session.add(salary)
    salary.basic = form.basic.data or 0
    salary.hra = form.hra.data or 0
    salary.conveyance = form.conveyance.data or 0
    salary.medical = form.medical.data or 0
    salary.special_allowance = form.special_allowance.data or 0
    salary.variable_pay = form.variable_pay.data or 0
    salary.pf_percent = form.pf_percent.data or 0
    salary.professional_tax = form.professional_tax.data or 0
    salary.income_tax_percent = form.income_tax_percent.data or 0
    salary.other_deduction = form.other_deduction.data or 0
    salary.overtime_multiplier = form.overtime_multiplier.data or 1.5
    return salary


@hr_bp.get("/")
@roles_required("hr", "admin")
def dashboard():
    today = date.today()
    total = Employee.query.filter(Employee.status != "inactive").count()
    present = Attendance.query.filter(Attendance.attendance_date == today, Attendance.status.in_(["present", "late", "half_day"])).count()
    pending_leaves = LeaveRequest.query.filter_by(status="pending").count()
    current_period = PayrollPeriod.query.filter_by(year=today.year, month=today.month).first()
    payroll_total = 0
    if current_period:
        payroll_total = db.session.query(db.func.coalesce(db.func.sum(PayrollEntry.net_pay), 0)).filter_by(period_id=current_period.id).scalar()
    return render_template(
        "hr/dashboard.html", total=total, present=present, pending_leaves=pending_leaves,
        payroll_total=float(payroll_total or 0), attendance_chart=attendance_chart(today.year, today.month),
        headcount_chart=department_headcount(), payroll_chart=payroll_trend(), current_period=current_period,
    )


@hr_bp.get("/employees")
@roles_required("hr", "admin")
def employees():
    query = Employee.query.join(Employee.user)
    search = request.args.get("q", "").strip()
    department_id = request.args.get("department", type=int)
    status = request.args.get("status", "active")
    if search:
        term = f"%{search}%"
        query = query.filter(db.or_(Employee.employee_code.ilike(term), User.full_name.ilike(term), User.email.ilike(term)))
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if status != "all":
        query = query.filter(Employee.status == status)
    items = query.order_by(Employee.employee_code).all()
    departments = Department.query.order_by(Department.name).all()
    return render_template("hr/employees.html", employees=items, departments=departments, search=search, department_id=department_id, status=status)


@hr_bp.route("/employees/new", methods=["GET", "POST"])
@roles_required("hr", "admin")
def employee_create():
    form = EmployeeForm()
    configure_employee_form(form)
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            form.email.errors.append("An account with this email already exists.")
        elif Employee.query.filter_by(employee_code=form.employee_code.data.strip().upper()).first():
            form.employee_code.errors.append("Employee code already exists.")
        elif not form.password.data:
            form.password.errors.append("An initial password is required for a new employee.")
        else:
            user = User(email=email, full_name=form.full_name.data.strip(), role=form.role.data, is_active=form.status.data != "inactive")
            user.set_password(form.password.data)
            employee = Employee(
                user=user, employee_code=form.employee_code.data.strip().upper(), department_id=form.department_id.data,
                manager_id=form.manager_id.data or None, designation=form.designation.data.strip(),
                date_of_joining=form.date_of_joining.data, employment_type=form.employment_type.data, status=form.status.data,
            )
            db.session.add_all([user, employee])
            salary_from_form(employee, form, new=True)
            db.session.flush()
            for leave_type in LeaveType.query.filter_by(is_active=True).all():
                db.session.add(LeaveBalance(employee_id=employee.id, leave_type_id=leave_type.id, year=date.today().year, allocated_days=leave_type.default_days))
            log_action("employee_created", "employee", employee.id, {"code": employee.employee_code})
            db.session.commit()
            flash("Employee created successfully.", "success")
            return redirect(url_for("hr.employees"))
    return render_template("hr/employee_form.html", form=form, title="Add employee", is_new=True)


@hr_bp.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@roles_required("hr", "admin")
def employee_edit(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    salary = employee.salary_structures.filter_by(is_active=True).order_by(SalaryStructure.effective_from.desc()).first()
    form = EmployeeForm()
    configure_employee_form(form)
    if request.method == "GET":
        form.full_name.data = employee.user.full_name
        form.email.data = employee.user.email
        form.employee_code.data = employee.employee_code
        form.department_id.data = employee.department_id
        form.manager_id.data = employee.manager_id or 0
        form.designation.data = employee.designation
        form.role.data = employee.user.role
        form.date_of_joining.data = employee.date_of_joining
        form.employment_type.data = employee.employment_type
        form.status.data = employee.status
        if salary:
            for name in ["basic", "hra", "conveyance", "medical", "special_allowance", "variable_pay", "pf_percent", "professional_tax", "income_tax_percent", "other_deduction", "overtime_multiplier"]:
                getattr(form, name).data = getattr(salary, name)
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        duplicate_user = User.query.filter(User.email == email, User.id != employee.user_id).first()
        duplicate_code = Employee.query.filter(Employee.employee_code == form.employee_code.data.strip().upper(), Employee.id != employee.id).first()
        if duplicate_user:
            form.email.errors.append("Another account uses this email.")
        elif duplicate_code:
            form.employee_code.errors.append("Another employee uses this code.")
        elif form.manager_id.data == employee.id:
            form.manager_id.errors.append("An employee cannot report to themselves.")
        else:
            employee.user.full_name = form.full_name.data.strip()
            employee.user.email = email
            employee.user.role = form.role.data
            employee.user.is_active = form.status.data != "inactive"
            if form.password.data:
                employee.user.set_password(form.password.data)
            employee.employee_code = form.employee_code.data.strip().upper()
            employee.department_id = form.department_id.data
            employee.manager_id = form.manager_id.data or None
            employee.designation = form.designation.data.strip()
            employee.date_of_joining = form.date_of_joining.data
            employee.employment_type = form.employment_type.data
            employee.status = form.status.data
            salary_from_form(employee, form)
            log_action("employee_updated", "employee", employee.id)
            db.session.commit()
            flash("Employee updated.", "success")
            return redirect(url_for("hr.employees"))
    return render_template("hr/employee_form.html", form=form, title="Edit employee", employee=employee, is_new=False)


@hr_bp.post("/employees/<int:employee_id>/deactivate")
@roles_required("hr", "admin")
def employee_deactivate(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    employee.status = "inactive"
    employee.user.is_active = False
    log_action("employee_deactivated", "employee", employee.id)
    db.session.commit()
    flash("Employee account deactivated.", "success")
    return redirect(url_for("hr.employees"))


@hr_bp.route("/shifts", methods=["GET", "POST"])
@roles_required("hr", "admin")
def shifts():
    form = ShiftForm()
    if form.validate_on_submit():
        code = form.code.data.strip().upper()
        if Shift.query.filter(db.or_(Shift.code == code, Shift.name == form.name.data.strip())).first():
            flash("Shift name or code already exists.", "danger")
        else:
            shift = Shift(name=form.name.data.strip(), code=code)
            form.populate_obj(shift)
            shift.code = code
            db.session.add(shift)
            log_action("shift_created", "shift", None, {"code": code})
            db.session.commit()
            flash("Shift created.", "success")
            return redirect(url_for("hr.shifts"))
    items = Shift.query.order_by(Shift.name).all()
    return render_template("hr/shifts.html", form=form, shifts=items)


@hr_bp.route("/holidays", methods=["GET", "POST"])
@roles_required("hr", "admin")
def holidays():
    form = HolidayForm()
    if form.validate_on_submit():
        if Holiday.query.filter_by(holiday_date=form.holiday_date.data).first():
            flash("A holiday already exists on this date.", "danger")
        else:
            item = Holiday()
            form.populate_obj(item)
            db.session.add(item)
            log_action("holiday_created", "holiday", None, {"date": item.holiday_date})
            db.session.commit()
            flash("Holiday added.", "success")
            return redirect(url_for("hr.holidays"))
    year = request.args.get("year", date.today().year, type=int)
    items = Holiday.query.filter(db.extract("year", Holiday.holiday_date) == year).order_by(Holiday.holiday_date).all()
    return render_template("hr/holidays.html", form=form, holidays=items, year=year)


@hr_bp.post("/holidays/<int:holiday_id>/delete")
@roles_required("hr", "admin")
def holiday_delete(holiday_id):
    item = Holiday.query.get_or_404(holiday_id)
    log_action("holiday_deleted", "holiday", item.id, {"date": item.holiday_date})
    db.session.delete(item)
    db.session.commit()
    flash("Holiday deleted.", "success")
    return redirect(url_for("hr.holidays"))


@hr_bp.route("/leave-types", methods=["GET", "POST"])
@roles_required("hr", "admin")
def leave_types():
    form = LeaveTypeForm()
    if form.validate_on_submit():
        code = form.code.data.strip().upper()
        if LeaveType.query.filter(db.or_(LeaveType.code == code, LeaveType.name == form.name.data.strip())).first():
            flash("Leave type name or code already exists.", "danger")
        else:
            item = LeaveType()
            form.populate_obj(item)
            item.code = code
            db.session.add(item)
            db.session.flush()
            for employee in Employee.query.filter(Employee.status != "inactive").all():
                if not LeaveBalance.query.filter_by(employee_id=employee.id, leave_type_id=item.id, year=date.today().year).first():
                    db.session.add(LeaveBalance(employee_id=employee.id, leave_type_id=item.id, year=date.today().year, allocated_days=item.default_days))
            log_action("leave_type_created", "leave_type", item.id)
            db.session.commit()
            flash("Leave type created and balances initialized.", "success")
            return redirect(url_for("hr.leave_types"))
    items = LeaveType.query.order_by(LeaveType.name).all()
    return render_template("hr/leave_types.html", form=form, leave_types=items)


@hr_bp.route("/payroll", methods=["GET", "POST"])
@roles_required("hr", "admin")
def payroll():
    form = PayrollPeriodForm()
    if form.validate_on_submit():
        if PayrollPeriod.query.filter_by(year=form.year.data, month=form.month.data).first():
            flash("This payroll period already exists.", "warning")
        else:
            period = PayrollPeriod(year=form.year.data, month=form.month.data, notes=form.notes.data)
            db.session.add(period)
            log_action("payroll_period_created", "payroll_period", None, {"year": period.year, "month": period.month})
            db.session.commit()
            flash("Payroll period created in draft status.", "success")
            return redirect(url_for("hr.payroll_period", period_id=period.id))
    periods = PayrollPeriod.query.order_by(PayrollPeriod.year.desc(), PayrollPeriod.month.desc()).all()
    period_totals = {
        p.id: float(db.session.query(db.func.coalesce(db.func.sum(PayrollEntry.net_pay), 0)).filter_by(period_id=p.id).scalar() or 0)
        for p in periods
    }
    return render_template("hr/payroll.html", form=form, periods=periods, period_totals=period_totals)


@hr_bp.get("/payroll/<int:period_id>")
@roles_required("hr", "admin")
def payroll_period(period_id):
    period = PayrollPeriod.query.get_or_404(period_id)
    entries = period.entries.join(PayrollEntry.employee).order_by(Employee.employee_code).all()
    total_gross = sum(float(e.gross_pay) for e in entries)
    total_net = sum(float(e.net_pay) for e in entries)
    return render_template("hr/payroll_period.html", period=period, entries=entries, total_gross=total_gross, total_net=total_net)


@hr_bp.post("/payroll/<int:period_id>/generate")
@roles_required("hr", "admin")
def payroll_generate(period_id):
    period = PayrollPeriod.query.get_or_404(period_id)
    if period.status in {"approved", "paid"}:
        flash("Approved or paid payroll cannot be regenerated.", "danger")
        return redirect(url_for("hr.payroll_period", period_id=period.id))
    generated, skipped = generate_period(period)
    period.status = "generated"
    period.generated_by_user_id = current_user.id
    period.generated_at = utcnow()
    log_action("payroll_generated", "payroll_period", period.id, {"generated": generated, "skipped": skipped})
    db.session.commit()
    message = f"Generated payroll for {generated} employees."
    if skipped:
        message += f" Skipped without salary structure: {', '.join(skipped)}."
    flash(message, "success" if not skipped else "warning")
    return redirect(url_for("hr.payroll_period", period_id=period.id))


@hr_bp.post("/payroll/<int:period_id>/approve")
@roles_required("hr", "admin")
def payroll_approve(period_id):
    period = PayrollPeriod.query.get_or_404(period_id)
    if period.status != "generated":
        flash("Generate payroll before approval.", "warning")
    else:
        period.status = "approved"
        period.approved_by_user_id = current_user.id
        for entry in period.entries.all():
            notify_user(entry.employee.user_id, "Payslip available", f"Your payslip for {period.label} is ready.", "success", url_for("employee.payslips"))
        log_action("payroll_approved", "payroll_period", period.id)
        db.session.commit()
        flash("Payroll approved and employees notified.", "success")
    return redirect(url_for("hr.payroll_period", period_id=period.id))


@hr_bp.post("/payroll/<int:period_id>/mark-paid")
@roles_required("hr", "admin")
def payroll_mark_paid(period_id):
    period = PayrollPeriod.query.get_or_404(period_id)
    if period.status != "approved":
        flash("Only approved payroll can be marked paid.", "warning")
    else:
        period.status = "paid"
        for entry in period.entries.all():
            entry.payment_status = "paid"
            entry.paid_at = utcnow()
        log_action("payroll_marked_paid", "payroll_period", period.id)
        db.session.commit()
        flash("Payroll marked as paid.", "success")
    return redirect(url_for("hr.payroll_period", period_id=period.id))


@hr_bp.get("/payroll/entry/<int:entry_id>.pdf")
@roles_required("hr", "admin")
def payroll_pdf(entry_id):
    entry = PayrollEntry.query.get_or_404(entry_id)
    pdf = build_payslip_pdf(entry, current_app.config["COMPANY_NAME"], current_app.config["COMPANY_ADDRESS"])
    log_action("payslip_downloaded_hr", "payroll_entry", entry.id)
    db.session.commit()
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name=f"payslip-{entry.employee.employee_code}-{entry.period.year}-{entry.period.month:02d}.pdf")


@hr_bp.get("/reports/attendance.csv")
@roles_required("hr", "admin")
def attendance_report_csv():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)
    start, end = month_range(year, month)
    records = Attendance.query.filter(Attendance.attendance_date.between(start, end)).join(Attendance.employee).order_by(Attendance.attendance_date, Employee.employee_code).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee Code", "Employee", "Department", "Date", "Status", "Check In", "Check Out", "Work Hours", "Late Minutes", "Overtime Hours"])
    for r in records:
        writer.writerow([r.employee.employee_code, r.employee.display_name, r.employee.department.name, r.attendance_date.isoformat(), r.status, r.check_in or "", r.check_out or "", round(r.work_minutes/60, 2), r.late_minutes, round(r.overtime_minutes/60, 2)])
    log_action("attendance_report_exported", details={"year": year, "month": month})
    db.session.commit()
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename=attendance-{year}-{month:02d}.csv"})


@hr_bp.get("/reports/payroll/<int:period_id>.csv")
@roles_required("hr", "admin")
def payroll_report_csv(period_id):
    period = PayrollPeriod.query.get_or_404(period_id)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee Code", "Employee", "Department", "Attendance Days", "Paid Leave", "Unpaid Days", "Overtime Hours", "Gross Pay", "Deductions", "Net Pay", "Status"])
    for e in period.entries.join(PayrollEntry.employee).order_by(Employee.employee_code).all():
        writer.writerow([e.employee.employee_code, e.employee.display_name, e.employee.department.name, e.attendance_days, e.paid_leave_days, e.unpaid_leave_days, e.overtime_hours, e.gross_pay, e.total_deductions, e.net_pay, e.payment_status])
    log_action("payroll_report_exported", "payroll_period", period.id)
    db.session.commit()
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename=payroll-{period.year}-{period.month:02d}.csv"})


@hr_bp.route("/attendance/manage", methods=["GET", "POST"])
@roles_required("hr", "admin")
def attendance_manage():
    """Manual attendance entry, corrections and monthly attendance chart."""
    allowed = {"present", "absent", "late", "half_day", "leave", "holiday"}
    selected_day = date.today()
    raw_day = request.values.get("attendance_date", date.today().isoformat())
    try:
        selected_day = date.fromisoformat(raw_day)
    except ValueError:
        flash("Invalid attendance date.", "danger")
    employees = Employee.query.filter(Employee.status != "inactive").order_by(Employee.employee_code).all()
    if request.method == "POST":
        try:
            employee_id = int(request.form.get("employee_id", "0"))
            employee = Employee.query.filter(Employee.id == employee_id, Employee.status != "inactive").first()
            status = request.form.get("status", "")
            if not employee or status not in allowed:
                raise ValueError("Select a valid employee and attendance status.")
            if selected_day > date.today():
                raise ValueError("Future attendance cannot be recorded.")
            if selected_day < employee.date_of_joining:
                raise ValueError("Attendance date precedes the employee joining date.")
            cin = request.form.get("check_in", "").strip()
            cout = request.form.get("check_out", "").strip()
            if status in {"absent", "leave", "holiday"} and (cin or cout):
                raise ValueError("Absent, leave and holiday records cannot have check-in/out times.")
            if bool(cin) != bool(cout):
                raise ValueError("Enter both check-in and check-out, or leave both blank.")
            check_in = datetime.combine(selected_day, datetime.strptime(cin, "%H:%M").time()) if cin else None
            check_out = datetime.combine(selected_day, datetime.strptime(cout, "%H:%M").time()) if cout else None
            if check_in and check_out <= check_in:
                raise ValueError("Check-out must be later than check-in on the same day.")
            from ...services.attendance_service import active_shift_for
            shift = active_shift_for(employee.id, selected_day)
            worked = max(0, int((check_out - check_in).total_seconds() // 60) - (shift.break_minutes if shift else 0)) if check_in else 0
            late = max(0, int((check_in - datetime.combine(selected_day, shift.start_time)).total_seconds() // 60)) if check_in and shift and check_in > datetime.combine(selected_day, shift.start_time) + timedelta(minutes=shift.grace_minutes) else 0
            overtime = max(0, worked - shift.overtime_threshold_minutes) if shift and check_in else 0
            record = Attendance.query.filter_by(employee_id=employee.id, attendance_date=selected_day).first()
            before = {"status": record.status, "check_in": str(record.check_in), "check_out": str(record.check_out)} if record else None
            if not record:
                record = Attendance(employee_id=employee.id, attendance_date=selected_day)
                db.session.add(record)
            record.status = status
            record.check_in, record.check_out = check_in, check_out
            record.work_minutes, record.late_minutes, record.overtime_minutes = worked, late, overtime
            record.source = "manual"
            record.notes = request.form.get("notes", "").strip()[:255]
            db.session.flush()
            log_action("attendance_manually_saved", "attendance", record.id, {"employee": employee.employee_code, "date": selected_day.isoformat(), "before": before, "after": {"status": status, "check_in": str(check_in), "check_out": str(check_out)}, "notes": record.notes})
            db.session.commit()
            flash("Attendance saved. Regenerate any unapproved payroll preview to reflect changes.", "success")
            return redirect(url_for("hr.attendance_manage", attendance_date=selected_day.isoformat(), employee_id=employee.id))
        except (ValueError, TypeError) as exc:
            db.session.rollback()
            flash(str(exc), "danger")
    month_start, month_end = month_range(selected_day.year, selected_day.month)
    records = Attendance.query.filter(Attendance.attendance_date.between(month_start, month_end)).all()
    counts = {k: sum(1 for row in records if row.status == k) for k in sorted(allowed)}
    selected_employee = request.args.get("employee_id", type=int)
    existing = Attendance.query.filter_by(employee_id=selected_employee, attendance_date=selected_day).first() if selected_employee else None
    recent = Attendance.query.filter_by(attendance_date=selected_day).order_by(Attendance.employee_id).limit(100).all()
    return render_template("hr/attendance_manage.html", employees=employees, selected_day=selected_day, selected_employee=selected_employee, existing=existing, recent=recent, counts=counts)
