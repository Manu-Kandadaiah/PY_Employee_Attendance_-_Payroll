from ..extensions import db
from .mixins import TimestampMixin


class SalaryStructure(TimestampMixin, db.Model):
    __tablename__ = "salary_structures"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    effective_from = db.Column(db.Date, nullable=False)
    basic = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    hra = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    conveyance = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    medical = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    special_allowance = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    variable_pay = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    pf_percent = db.Column(db.Numeric(5, 2), default=12, nullable=False)
    professional_tax = db.Column(db.Numeric(10, 2), default=200, nullable=False)
    income_tax_percent = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    other_deduction = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    overtime_multiplier = db.Column(db.Numeric(5, 2), default=1.5, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    employee = db.relationship("Employee", back_populates="salary_structures")

    @property
    def monthly_gross(self):
        return sum(float(value or 0) for value in [self.basic, self.hra, self.conveyance, self.medical, self.special_allowance, self.variable_pay])


class PayrollPeriod(TimestampMixin, db.Model):
    __tablename__ = "payroll_periods"
    __table_args__ = (db.UniqueConstraint("year", "month", name="uq_payroll_period"),)

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False, index=True)
    working_days = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.Enum("draft", "generated", "approved", "paid", name="payroll_period_statuses"), default="draft", nullable=False)
    generated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    generated_at = db.Column(db.DateTime)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    notes = db.Column(db.String(255))

    entries = db.relationship("PayrollEntry", back_populates="period", cascade="all, delete-orphan", lazy="dynamic")
    generated_by = db.relationship("User", foreign_keys=[generated_by_user_id])
    approved_by = db.relationship("User", foreign_keys=[approved_by_user_id])

    @property
    def label(self):
        import calendar
        return f"{calendar.month_name[self.month]} {self.year}"


class PayrollEntry(TimestampMixin, db.Model):
    __tablename__ = "payroll_entries"
    __table_args__ = (db.UniqueConstraint("period_id", "employee_id", name="uq_period_employee_payroll"),)

    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey("payroll_periods.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_days = db.Column(db.Numeric(6, 2), default=0, nullable=False)
    paid_leave_days = db.Column(db.Numeric(6, 2), default=0, nullable=False)
    unpaid_leave_days = db.Column(db.Numeric(6, 2), default=0, nullable=False)
    overtime_hours = db.Column(db.Numeric(8, 2), default=0, nullable=False)
    basic = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    hra = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    allowances = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    overtime_pay = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    gross_pay = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    pf_deduction = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    professional_tax = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    income_tax = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    other_deductions = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    total_deductions = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    net_pay = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    payment_status = db.Column(db.Enum("pending", "processed", "paid", name="payment_statuses"), default="pending", nullable=False)
    paid_at = db.Column(db.DateTime)
    payslip_path = db.Column(db.String(255))

    period = db.relationship("PayrollPeriod", back_populates="entries")
    employee = db.relationship("Employee", back_populates="payroll_entries")
    line_items = db.relationship("PayrollLineItem", back_populates="payroll_entry", cascade="all, delete-orphan", lazy="selectin")


class PayrollLineItem(TimestampMixin, db.Model):
    __tablename__ = "payroll_line_items"

    id = db.Column(db.Integer, primary_key=True)
    payroll_entry_id = db.Column(db.Integer, db.ForeignKey("payroll_entries.id", ondelete="CASCADE"), nullable=False)
    category = db.Column(db.Enum("earning", "deduction", name="payroll_line_categories"), nullable=False)
    code = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(12, 2), default=0, nullable=False)

    payroll_entry = db.relationship("PayrollEntry", back_populates="line_items")
