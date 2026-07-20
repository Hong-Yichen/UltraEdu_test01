from datetime import datetime, timedelta, timezone

from flask import render_template
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.models.academic import Enrollment
from app.models.assignment import Assignment


@student_bp.route("/planner")
@login_required
@role_required("student")
def planner():
    class_ids = [e.class_group_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()]
    assignments = []
    if class_ids:
        assignments = (
            Assignment.query.filter(
                Assignment.class_group_id.in_(class_ids), Assignment.published_at.isnot(None)
            )
            .order_by(Assignment.due_date)
            .all()
        )

    now = datetime.now(timezone.utc)
    today = now.date()
    week_end = today + timedelta(days=7)

    due_today, due_this_week, upcoming_projects, upcoming_exams = [], [], [], []
    for a in assignments:
        if a.due_date is None:
            continue
        due_date = a.due_date.date() if hasattr(a.due_date, "date") else a.due_date
        if due_date == today:
            due_today.append(a)
        elif today < due_date <= week_end:
            due_this_week.append(a)
        if a.is_group_assignment and due_date >= today:
            upcoming_projects.append(a)
        if a.is_exam and due_date >= today:
            upcoming_exams.append(a)

    return render_template(
        "student/planner.html",
        due_today=due_today,
        due_this_week=due_this_week,
        upcoming_projects=upcoming_projects,
        upcoming_exams=upcoming_exams,
    )
