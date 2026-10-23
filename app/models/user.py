from flask_login import UserMixin
from ..extensions import bcrypt, db
from .mixins import TimestampMixin, utcnow


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "hr", "manager", "employee", name="user_roles"), nullable=False, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login_at = db.Column(db.DateTime)

    employee_profile = db.relationship(
        "Employee", foreign_keys="Employee.user_id", back_populates="user", uselist=False
    )
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def has_role(self, *roles):
        return self.role in roles

    def touch_login(self):
        self.last_login_at = utcnow()

    def __repr__(self):
        return f"<User {self.email}>"
