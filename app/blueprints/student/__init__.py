from flask import Blueprint
from flask_login import current_user

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.before_request
def _check_exam_lockdown_restrictions():
    if not current_user.is_authenticated:
        return None
    from app.services.exam_lockdown_guard import enforce_restrictions

    return enforce_restrictions(current_user)


from app.blueprints.student import (  # noqa: E402,F401
    dashboard,
    notes,
    assignments,
    exam_lockdown,
    storybooks,
    groups,
    bookmarks,
    planner,
    progress,
    calendar,
    messages,
    textbooks,
    examinations,
)
