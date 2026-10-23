import json
from flask import request
from flask_login import current_user
from ..extensions import db
from ..models import AuditLog
from ..models.mixins import utcnow


def log_action(action, entity_type=None, entity_id=None, details=None):
    log = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=json.dumps(details, default=str) if isinstance(details, (dict, list)) else details,
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        user_agent=(request.user_agent.string or "")[:255],
        created_at=utcnow(),
    )
    db.session.add(log)
