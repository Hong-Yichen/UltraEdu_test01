from flask import render_template
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.models.assignment import Assignment
from app.models.resource import Resource
from app.services.exam_lockdown_guard import get_active_exam_session, get_active_lockdown_session


@student_bp.route("/exam-active")
@login_required
@role_required("student")
def exam_active():
    session_ = get_active_exam_session(current_user)
    return render_template("student/exam_active.html", exam_session=session_)


@student_bp.route("/lockdown")
@login_required
@role_required("student")
def lockdown():
    session_ = get_active_lockdown_session(current_user)
    assignments = []
    resources = []
    if session_ is not None:
        assignments = Assignment.query.filter(
            Assignment.class_group_id == session_.class_group_id,
            Assignment.published_at.isnot(None),
        ).all()
        if session_.allowed_resource_ids:
            resources = Resource.query.filter(
                Resource.id.in_(session_.allowed_resource_ids)
            ).all()
    return render_template(
        "student/lockdown.html", lockdown_session=session_, assignments=assignments, resources=resources
    )


@student_bp.route("/calculator")
@login_required
@role_required("student")
def calculator():
    return render_template("student/calculator.html")
