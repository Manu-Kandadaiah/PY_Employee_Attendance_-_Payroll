from ..extensions import db
from .mixins import TimestampMixin


class Shift(TimestampMixin, db.Model):
    __tablename__ = "shifts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    grace_minutes = db.Column(db.Integer, default=10, nullable=False)
    break_minutes = db.Column(db.Integer, default=60, nullable=False)
    minimum_half_day_minutes = db.Column(db.Integer, default=240, nullable=False)
    overtime_threshold_minutes = db.Column(db.Integer, default=480, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    assignments = db.relationship("ShiftAssignment", back_populates="shift", cascade="all, delete-orphan", lazy="dynamic")


class ShiftAssignment(TimestampMixin, db.Model):
    __tablename__ = "shift_assignments"
    __table_args__ = (db.Index("ix_shift_assignment_dates", "employee_id", "effective_from", "effective_to"),)

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey("shifts.id"), nullable=False)
    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date)

    employee = db.relationship("Employee", back_populates="shift_assignments")
    shift = db.relationship("Shift", back_populates="assignments")


class Attendance(TimestampMixin, db.Model):
    __tablename__ = "attendance"
    __table_args__ = (db.UniqueConstraint("employee_id", "attendance_date", name="uq_employee_attendance_date"),)

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_date = db.Column(db.Date, nullable=False, index=True)
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    status = db.Column(db.Enum("present", "late", "half_day", "absent", "leave", "holiday", "weekend", name="attendance_statuses"), default="present", nullable=False)
    work_minutes = db.Column(db.Integer, default=0, nullable=False)
    late_minutes = db.Column(db.Integer, default=0, nullable=False)
    overtime_minutes = db.Column(db.Integer, default=0, nullable=False)
    source = db.Column(db.Enum("web", "mobile", "manual", "biometric", name="attendance_sources"), default="web", nullable=False)
    notes = db.Column(db.String(255))

    employee = db.relationship("Employee", back_populates="attendance_records")
    overtime_request = db.relationship("OvertimeRequest", back_populates="attendance", uselist=False, cascade="all, delete-orphan")


class OvertimeRequest(TimestampMixin, db.Model):
    __tablename__ = "overtime_requests"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_id = db.Column(db.Integer, db.ForeignKey("attendance.id", ondelete="CASCADE"), unique=True, nullable=False)
    requested_minutes = db.Column(db.Integer, nullable=False)
    approved_minutes = db.Column(db.Integer, default=0, nullable=False)
    reason = db.Column(db.String(255))
    status = db.Column(db.Enum("pending", "approved", "rejected", name="overtime_statuses"), default="pending", nullable=False, index=True)
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    reviewer_comments = db.Column(db.String(255))

    employee = db.relationship("Employee")
    attendance = db.relationship("Attendance", back_populates="overtime_request")
    reviewed_by = db.relationship("User")
