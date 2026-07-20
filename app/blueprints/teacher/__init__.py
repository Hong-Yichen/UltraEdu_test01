from flask import Blueprint

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

from app.blueprints.teacher import (  # noqa: E402,F401
    dashboard,
    resources,
    announcements,
    worksheets,
    assignments,
    grading,
    exam_lockdown,
    storybooks,
    groups,
    analytics,
    calendar,
    messages,
    textbooks,
    model_answers,
    examinations,
)
