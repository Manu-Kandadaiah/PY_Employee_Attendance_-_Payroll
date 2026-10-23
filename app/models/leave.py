from ..extensions import db
from .mixins import TimestampMixin


class LeaveType(TimestampMixin, db.Model):
    __tablename__ = "leave_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    is_paid = db.Column(db.Boolean, default=True, nullable=False)
    default_days = db.Column(db.Numeric(6, 2), default=0, nullable=False)
    requires_document = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class LeaveBalance(TimestampMixin, db.Model):
    __tablename__ = "leave_balances"
    __table_args__ = (db.UniqueConstraint("employee_id", "leave_type_id", "year", name="uq_leave_balance_year"),)

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey("leave_types.id"), nullable=False)
    year = db.Column(db.Integer, nullable=False, index=True)
    allocated_days = db.Column(db.Numeric(6, 2), default=0, nullable=False)
    used_days = db.Column(db.Numeric(6, 2), default=0, nullable=False)
    pending_days = db.Column(db.Numeric(6, 2), default=0, nullable=False)

    employee = db.relationship("Employee")
    leave_type = db.relationship("LeaveType")

    @property
    def available_days(self):
        return float(self.allocated_days or 0) - float(self.used_days or 0) - float(self.pending_days or 0)


class LeaveRequest(TimestampMixin, db.Model):
    __tablename__ = "leave_requests"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type_id = db.Column(db.Integer, db.ForeignKey("leave_types.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False)
    days = db.Column(db.Numeric(6, 2), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum("pending", "approved", "rejected", "cancelled", name="leave_statuses"), default="pending", nullable=False, index=True)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    reviewer_comments = db.Column(db.String(255))
    reviewed_at = db.Column(db.DateTime)

    employee = db.relationship("Employee", back_populates="leave_requests")
    leave_type = db.relationship("LeaveType")
    approved_by = db.relationship("User")


class Holiday(TimestampMixin, db.Model):
    __tablename__ = "holidays"

    id = db.Column(db.Integer, primary_key=True)
    holiday_date = db.Column(db.Date, unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    is_optional = db.Column(db.Boolean, default=False, nullable=False)
