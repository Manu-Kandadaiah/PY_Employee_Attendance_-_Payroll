from ..extensions import db
from .mixins import TimestampMixin


class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum("info", "success", "warning", "danger", name="notification_categories"), default="info", nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)

    user = db.relationship("User", back_populates="notifications")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(80))
    entity_id = db.Column(db.String(80))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, index=True)

    user = db.relationship("User")
