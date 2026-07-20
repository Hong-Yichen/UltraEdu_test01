from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import LoginForm
from app.models.user import User


def _redirect_to_dashboard(user):
    if user.is_teacher:
        return redirect(url_for("teacher.dashboard"))
    return redirect(url_for("student.dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_to_dashboard(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "error")
        elif not user.is_active:
            flash("This account is deactivated.", "error")
        else:
            login_user(user, remember=form.remember.data)
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return _redirect_to_dashboard(user)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))
