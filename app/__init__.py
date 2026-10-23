import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template
from sqlalchemy import event

load_dotenv()  # Load .env BEFORE importing config, which reads environment variables.
from config import config_by_name
from .extensions import bcrypt, csrf, db, limiter, login_manager, migrate


def create_app(config_name=None):
    load_dotenv()
    app = Flask(__name__)
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))
    if config_name != "testing":
        session_secret = str(app.config.get("SECRET_KEY") or "")
        if len(session_secret) < 24 or session_secret.startswith("REPLACE_"):
            raise RuntimeError("Configure a strong SECRET_KEY (24+ characters) in .env before starting PyCareer.")

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["PAYSLIP_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    # Enforce referential integrity for local SQLite connections.
    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            @event.listens_for(db.engine, "connect")
            def enable_sqlite_foreign_keys(connection, _record):
                cursor = connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to continue."
    login_manager.login_message_category = "warning"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .blueprints.main.routes import main_bp
    from .blueprints.auth.routes import auth_bp
    from .blueprints.employee.routes import employee_bp
    from .blueprints.manager.routes import manager_bp
    from .blueprints.hr.routes import hr_bp
    from .blueprints.admin.routes import admin_bp
    from .blueprints.api.routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(employee_bp, url_prefix="/employee")
    app.register_blueprint(manager_bp, url_prefix="/manager")
    app.register_blueprint(hr_bp, url_prefix="/hr")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    from .blueprints.analytics.routes import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix="/analytics")

    @app.context_processor
    def inject_globals():
        from .models import Notification
        unread = 0
        try:
            from flask_login import current_user
            if current_user.is_authenticated:
                unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        except Exception:
            pass
        return {"unread_notification_count": unread}

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    from .cli import register_commands
    register_commands(app)
    return app
