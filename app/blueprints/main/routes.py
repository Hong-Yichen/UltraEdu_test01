from flask import redirect, url_for
from flask_login import current_user

from app.blueprints.main import main_bp


@main_bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if current_user.is_teacher:
        return redirect(url_for("teacher.dashboard"))
    return redirect(url_for("student.dashboard"))
