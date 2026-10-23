from ..extensions import db
from .mixins import TimestampMixin


class Department(TimestampMixin, db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    employees = db.relationship("Employee", back_populates="department", lazy="dynamic")


class Employee(TimestampMixin, db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False, index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True, index=True)
    designation = db.Column(db.String(120), nullable=False)
    date_of_joining = db.Column(db.Date, nullable=False)
    employment_type = db.Column(db.Enum("full_time", "part_time", "contract", "intern", name="employment_types"), default="full_time", nullable=False)
    status = db.Column(db.Enum("active", "probation", "notice", "inactive", name="employee_statuses"), default="active", nullable=False, index=True)
    phone = db.Column(db.String(25))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(120))
    bank_name = db.Column(db.String(120))
    bank_account = db.Column(db.String(60))
    bank_ifsc = db.Column(db.String(20))
    pan_number = db.Column(db.String(20))
    uan_number = db.Column(db.String(30))

    user = db.relationship("User", foreign_keys=[user_id], back_populates="employee_profile")
    department = db.relationship("Department", back_populates="employees")
    manager = db.relationship("Employee", remote_side=[id], foreign_keys=[manager_id], back_populates="direct_reports")
    direct_reports = db.relationship("Employee", foreign_keys=[manager_id], back_populates="manager", lazy="dynamic")
    attendance_records = db.relationship("Attendance", back_populates="employee", cascade="all, delete-orphan", lazy="dynamic")
    leave_requests = db.relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan", lazy="dynamic")
    shift_assignments = db.relationship("ShiftAssignment", back_populates="employee", cascade="all, delete-orphan", lazy="dynamic")
    salary_structures = db.relationship("SalaryStructure", back_populates="employee", cascade="all, delete-orphan", lazy="dynamic")
    payroll_entries = db.relationship("PayrollEntry", back_populates="employee", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def display_name(self):
        return self.user.full_name if self.user else self.employee_code
