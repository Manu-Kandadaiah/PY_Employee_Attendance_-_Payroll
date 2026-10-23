from urllib.parse import urljoin, urlparse
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required

from ...extensions import db, limiter
from ...forms import ChangePasswordForm, LoginForm
from ...models import User
from ...utils.audit import log_action

auth_bp = Blueprint("auth", __name__)


def is_safe_url(target):
    host_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in {"http", "https"} and host_url.netloc == test_url.netloc


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(db.func.lower(User.email) == form.email.data.strip().lower()).first()
        if user and user.is_active and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            user.touch_login()
            log_action("login", "user", user.id)
            db.session.commit()
            next_url = request.args.get("next")
            return redirect(next_url if next_url and is_safe_url(next_url) else url_for("main.dashboard"))
        flash("Invalid credentials or inactive account.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.post("/logout")
@login_required
def logout():
    log_action("logout", "user", current_user.id)
    db.session.commit()
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            log_action("password_changed", "user", current_user.id)
            db.session.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("main.dashboard"))
    return render_template("auth/change_password.html", form=form)
