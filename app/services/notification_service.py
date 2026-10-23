from ..extensions import db
from ..models import Notification, User


def notify_user(user_id, title, message, category="info", link=None, commit=False):
    item = Notification(user_id=user_id, title=title, message=message, category=category, link=link)
    db.session.add(item)
    if commit:
        db.session.commit()
    return item


def notify_roles(roles, title, message, category="info", link=None):
    users = User.query.filter(User.role.in_(roles), User.is_active.is_(True)).all()
    for user in users:
        notify_user(user.id, title, message, category, link)
    return len(users)
