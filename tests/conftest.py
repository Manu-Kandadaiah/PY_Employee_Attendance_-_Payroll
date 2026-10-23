from datetime import date, time
import pytest

from app import create_app
from app.extensions import db
from app.models import Department, Employee, LeaveBalance, LeaveType, SalaryStructure, Shift, ShiftAssignment, User


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        eng = Department(name="Engineering", code="ENG")
        hr_dept = Department(name="Human Resources", code="HR")
        db.session.add_all([eng, hr_dept])
        db.session.flush()

        shift = Shift(name="General", code="GEN", start_time=time(9), end_time=time(18), grace_minutes=10, break_minutes=60, minimum_half_day_minutes=240, overtime_threshold_minutes=480)
        leave = LeaveType(name="Casual Leave", code="CL", is_paid=True, default_days=12)
        db.session.add_all([shift, leave])

        def user(email, name, role, password="Password@123"):
            item = User(email=email, full_name=name, role=role, is_active=True)
            item.set_password(password)
            db.session.add(item)
            return item

        admin = user("admin@test.com", "Admin User", "admin")
        hr_user = user("hr@test.com", "HR User", "hr")
        manager_user = user("manager@test.com", "Manager User", "manager")
        employee_user = user("employee@test.com", "Employee User", "employee")
        db.session.flush()

        hr_emp = Employee(user=hr_user, employee_code="E001", department=hr_dept, designation="HR Executive", date_of_joining=date(2024,1,1))
        manager_emp = Employee(user=manager_user, employee_code="E002", department=eng, designation="Manager", date_of_joining=date(2023,1,1))
        employee_emp = Employee(user=employee_user, employee_code="E003", department=eng, manager=manager_emp, designation="Engineer", date_of_joining=date(2025,1,1))
        db.session.add_all([hr_emp, manager_emp, employee_emp])
        db.session.flush()
        for emp, basic in [(hr_emp, 50000), (manager_emp, 70000), (employee_emp, 40000)]:
            db.session.add(SalaryStructure(employee=emp, effective_from=emp.date_of_joining, basic=basic, hra=basic*0.4, conveyance=2000, special_allowance=5000, pf_percent=12, professional_tax=200, income_tax_percent=5, overtime_multiplier=1.5))
            db.session.add(ShiftAssignment(employee=emp, shift=shift, effective_from=emp.date_of_joining))
            db.session.add(LeaveBalance(employee=emp, leave_type=leave, year=date.today().year, allocated_days=12))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email, password="Password@123"):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=True)
