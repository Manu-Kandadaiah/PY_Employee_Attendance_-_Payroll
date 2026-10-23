from datetime import date, datetime, timedelta, time
import click
from flask.cli import with_appcontext

from .extensions import db
from .models import (
    Attendance, Department, Employee, Holiday, LeaveBalance, LeaveRequest, LeaveType,
    PayrollPeriod, SalaryStructure, Shift, ShiftAssignment, User,
)
from .services.payroll_service import generate_period


def register_commands(app):
    app.cli.add_command(init_db)
    app.cli.add_command(seed_demo)
    app.cli.add_command(create_admin)


@click.command("init-db")
@with_appcontext
def init_db():
    """Create database tables. Use migrations in long-lived production environments."""
    db.create_all()
    click.echo("Database tables created.")


@click.command("create-admin")
@click.option("--email", prompt=True)
@click.option("--name", prompt=True)
@click.password_option()
@with_appcontext
def create_admin(email, name, password):
    email = email.strip().lower()
    if User.query.filter_by(email=email).first():
        raise click.ClickException("Email already exists.")
    user = User(email=email, full_name=name.strip(), role="admin", is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo("Administrator created.")


@click.command("seed-demo")
@with_appcontext
def seed_demo():
    """Seed exactly 200 fictional employee profiles with linked payroll data.

    Repeatable: if PyCareer demo users are already present, this exits without
    adding duplicate records. Existing non-demo employee databases are never
    silently overwritten.
    """
    import os
    import random
    import secrets
    from calendar import monthrange
    from sqlalchemy import func
    from .models import PayrollEntry

    db.create_all()
    if User.query.filter_by(email="admin@pycareer.com").first():
        count = Employee.query.count()
        click.echo(f"PyCareer demo already exists ({count} employee profiles); nothing changed.")
        return
    if Employee.query.count() or User.query.count():
        raise click.ClickException("Database already contains users/employees. Seed only a fresh local demo database.")

    password = os.getenv("DEMO_PASSWORD", "")
    if len(password) < 12 or password.startswith("REPLACE_"):
        raise click.ClickException("Set DEMO_PASSWORD to a private value (12+ characters) in .env before seeding.")

    rng = random.Random(20261022)
    department_specs = [
        ("Engineering", "ENG", "Platform and application engineering"),
        ("Data & Analytics", "DATA", "Business intelligence and data solutions"),
        ("Product & Design", "PROD", "Digital product, UX and design"),
        ("Career Services", "CAREER", "Mentoring and career guidance"),
        ("Recruitment", "TALENT", "Talent acquisition and employer partnerships"),
        ("Learning & Content", "LEARN", "Technical education and learning content"),
        ("Finance & Operations", "OPS", "Business operations and payroll"),
        ("People & Culture", "PEOPLE", "People operations and HR"),
    ]
    departments = []
    for name, code, description in department_specs:
        item = Department(name=name, code=code, description=description)
        departments.append(item)
        db.session.add(item)

    shifts = [
        Shift(name="General Shift", code="GEN", start_time=time(9, 30), end_time=time(18, 0), grace_minutes=10, break_minutes=30, minimum_half_day_minutes=240, overtime_threshold_minutes=480),
        Shift(name="Early Support", code="EAR", start_time=time(8, 0), end_time=time(16, 30), grace_minutes=10, break_minutes=30, minimum_half_day_minutes=240, overtime_threshold_minutes=480),
        Shift(name="Late Support", code="LATE", start_time=time(11, 0), end_time=time(19, 30), grace_minutes=10, break_minutes=30, minimum_half_day_minutes=240, overtime_threshold_minutes=480),
    ]
    db.session.add_all(shifts)
    leave_types = [
        LeaveType(name="Casual Leave", code="CL", is_paid=True, default_days=12),
        LeaveType(name="Sick Leave", code="SL", is_paid=True, default_days=10),
        LeaveType(name="Earned Leave", code="EL", is_paid=True, default_days=18),
        LeaveType(name="Loss of Pay", code="LOP", is_paid=False, default_days=0),
    ]
    db.session.add_all(leave_types)
    db.session.flush()

    def user(email, name, role, demo=False):
        u = User(email=email, full_name=name, role=role, is_active=True)
        # Non-demo accounts get unique unknown random credentials; only the
        # four explicitly labeled demo roles are usable for the local tour.
        u.set_password(password if demo else secrets.token_urlsafe(28))
        db.session.add(u)
        return u

    user("admin@pycareer.com", "PyCareer Administrator", "admin", True)
    hr_user = user("hr@pycareer.com", "Ananya Rao", "hr", True)
    manager_user = user("manager@pycareer.com", "Rahul Menon", "manager", True)
    employee_user = user("employee@pycareer.com", "Neha Sharma", "employee", True)
    db.session.flush()

    def attach_emp(u, code, dept, job, joined, role_manager=None, status="active"):
        e = Employee(user=u, employee_code=code, department=dept, designation=job,
                     date_of_joining=joined, status=status, manager=role_manager,
                     employment_type="full_time")
        db.session.add(e)
        return e

    employees = [
        attach_emp(hr_user, "PYC0001", departments[7], "HR Operations Lead", date(2022, 4, 4)),
        attach_emp(manager_user, "PYC0002", departments[0], "Engineering Manager", date(2021, 8, 2)),
        attach_emp(employee_user, "PYC0003", departments[0], "Python Developer", date(2024, 1, 8)),
    ]
    db.session.flush()
    employees[2].manager = employees[1]
    managers = {0: employees[1], 7: employees[0]}

    first_names = ["Aarav", "Aditi", "Aditya", "Akash", "Ananya", "Anika", "Arjun", "Avni", "Dev", "Diya", "Eshan", "Isha", "Ishaan", "Kabir", "Kavya", "Kiran", "Krisha", "Manav", "Meera", "Mihir", "Naina", "Nikhil", "Pooja", "Pranav", "Priya", "Rhea", "Rohan", "Riya", "Sahil", "Sanjana", "Sanya", "Shaurya", "Tanvi", "Tara", "Varun", "Vedika", "Vihaan", "Yash"]
    last_names = ["Bhat", "Chandra", "Desai", "Ghosh", "Gupta", "Iyer", "Jain", "Joshi", "Kapoor", "Kulkarni", "Menon", "Mehta", "Nair", "Patel", "Pillai", "Rao", "Reddy", "Shah", "Sharma", "Singh", "Srinivasan", "Verma"]
    roles = {
        0: ["Software Engineer", "Senior Python Developer", "QA Engineer", "DevOps Engineer", "Frontend Developer", "Backend Developer"],
        1: ["Data Analyst", "BI Analyst", "Data Engineer", "Analytics Engineer"],
        2: ["Product Analyst", "UX Designer", "UI Designer", "Product Owner"],
        3: ["Career Coach", "Placement Specialist", "Student Success Associate"],
        4: ["Recruiter", "Talent Specialist", "Employer Partnerships Associate"],
        5: ["Curriculum Developer", "Python Trainer", "Content Specialist"],
        6: ["Finance Analyst", "Operations Executive", "Payroll Associate"],
        7: ["HR Executive", "People Operations Associate", "HR Coordinator"],
    }
    # Add one primary reporting manager for each department other than
    # Engineering and People & Culture; distribute their reports evenly.
    for department_index in (1, 2, 3, 4, 5, 6):
        number = len(employees) + 1
        name = f"{first_names[number % len(first_names)]} {last_names[(number * 7) % len(last_names)]}"
        u = user(f"staff{number:04d}@pycareer.com", name, "manager")
        emp = attach_emp(u, f"PYC{number:04d}", departments[department_index], "Team Lead", date(2022, 1 + department_index, 10))
        employees.append(emp)
        managers[department_index] = emp
    db.session.flush()

    for number in range(len(employees) + 1, 201):
        dept_i = (number * 13 + number // 7) % len(departments)
        first = first_names[(number * 11 + 3) % len(first_names)]
        last = last_names[(number * 7 + number // 11) % len(last_names)]
        name = f"{first} {last}"
        joined = date(rng.randint(2021, 2026), rng.randint(1, 9), rng.randint(1, 26))
        u = user(f"staff{number:04d}@pycareer.com", name, "employee")
        e = attach_emp(u, f"PYC{number:04d}", departments[dept_i], rng.choice(roles[dept_i]), joined, managers[dept_i], status="probation" if number % 19 == 0 else "active")
        employees.append(e)
    db.session.flush()
    assert len(employees) == 200

    today = date.today()
    for e in employees:
        # Salary brackets depend on job category, with deterministic variation.
        if e.user.role == "manager":
            basic = rng.choice([70000, 78000, 84000, 95000])
        elif e.user.role == "hr":
            basic = 68000
        else:
            basic = rng.choice([28000, 32000, 37000, 42000, 48000, 54000, 62000])
        db.session.add(SalaryStructure(employee=e, effective_from=e.date_of_joining,
            basic=basic, hra=round(basic * 0.40, 2), conveyance=2200, medical=1250,
            special_allowance=round(basic * 0.16), pf_percent=12, professional_tax=200,
            income_tax_percent=3 if basic < 50000 else 5,
            overtime_multiplier=1.5))
        dept_shift = shifts[1] if e.department.code == "CAREER" and int(e.employee_code[-2:]) % 3 == 0 else shifts[0]
        db.session.add(ShiftAssignment(employee=e, shift=dept_shift, effective_from=e.date_of_joining))
        for lt in leave_types:
            db.session.add(LeaveBalance(employee=e, leave_type=lt, year=today.year, allocated_days=lt.default_days))

    for hday, name in [(date(today.year, 1, 26), "Republic Day"), (date(today.year, 8, 15), "Independence Day"), (date(today.year, 10, 2), "Gandhi Jayanti")]:
        db.session.add(Holiday(holiday_date=hday, name=name, description="Demo holiday calendar"))

    # Cover full previous month and the current month to date, so the HR
    # dashboard, employee attendance and payroll are useful immediately.
    last_month_end = today.replace(day=1) - timedelta(days=1)
    first_day = last_month_end.replace(day=1)
    attendance_count = 0
    day = first_day
    while day <= today:
        if day.weekday() < 5:
            for e in employees:
                if day < e.date_of_joining or rng.random() < 0.055:
                    continue
                minute = rng.choice([26, 31, 34, 38, 42, 48])
                checkin = datetime.combine(day, time(9, minute))
                checkout = datetime.combine(day, time(18, rng.choice([0, 10, 20, 40])))
                worked = max(0, int((checkout - checkin).total_seconds() // 60) - 30)
                db.session.add(Attendance(employee=e, attendance_date=day,
                    check_in=checkin, check_out=checkout,
                    status="late" if minute > 40 else "present",
                    work_minutes=worked,
                    late_minutes=max(0, minute - 30),
                    overtime_minutes=max(0, worked - 480),
                    source="manual", notes="Fictional demonstration record"))
                attendance_count += 1
        day += timedelta(days=1)

    leave_emp = employees[2]
    db.session.add(LeaveRequest(employee=leave_emp, leave_type=leave_types[0],
        start_date=today + timedelta(days=7), end_date=today + timedelta(days=8),
        days=2, reason="Fictional personal leave request", status="pending"))
    balance = LeaveBalance.query.filter_by(employee_id=leave_emp.id, leave_type_id=leave_types[0].id, year=today.year).first()
    if balance:
        balance.pending_days = 2

    db.session.commit()

    # Show a realistic but *not approved/paid* payroll statement for the
    # completed previous month. Generated status is a local demo only.
    period = PayrollPeriod(year=last_month_end.year, month=last_month_end.month,
        status="generated", generated_by_user_id=hr_user.id,
        generated_at=datetime.now(), notes="Synthetic PyCareer preview; not approved for payment")
    db.session.add(period)
    db.session.flush()
    generated, skipped = generate_period(period)
    db.session.commit()
    click.echo(f"Created 200 fictional employees, {len(departments)} departments, {attendance_count} attendance records, {generated} demo payroll entries.")
    click.echo("All accounts and email addresses are fictional. Demo users are admin, hr, manager, employee @pycareer.com")
    click.echo("Demo password: the private DEMO_PASSWORD value in your local .env. Never publish it.")
    if skipped:
        click.echo(f"Warning: {len(skipped)} payroll entries skipped for missing salary structures")
