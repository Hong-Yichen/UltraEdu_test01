from datetime import datetime

from flask import render_template
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.constants import NON_ACADEMIC_SUBJECT_CODES
from app.models.academic import ClassGroup, Timetable, Enrollment, Subject
from app.models.assignment import Assignment, Submission
from app.services.timetable_service import build_week_grid, DAY_NAMES


@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():
    today_dow = datetime.now().weekday()
    class_ids = [
        e.class_group_id
        for e in Enrollment.query.filter_by(student_id=current_user.id).all()
    ]
    classes = []
    today_timetable = []
    due_today = []
    upcoming_homework = []
    recent_grades = []
    if class_ids:
        classes = (
            ClassGroup.query.join(Subject, ClassGroup.subject_id == Subject.id)
            .filter(ClassGroup.id.in_(class_ids), Subject.code.notin_(NON_ACADEMIC_SUBJECT_CODES))
            .order_by(ClassGroup.name)
            .all()
        )
        today_timetable = (
            Timetable.query.filter(
                Timetable.class_group_id.in_(class_ids), Timetable.day_of_week == today_dow
            )
            .order_by(Timetable.period_number)
            .all()
        )

        assignments = Assignment.query.filter(
            Assignment.class_group_id.in_(class_ids), Assignment.published_at.isnot(None)
        ).all()
        today_date = datetime.now().date()
        due_today = [a for a in assignments if a.due_date and a.due_date.date() == today_date]
        upcoming_homework = sorted(
            [a for a in assignments if a.due_date and a.due_date.date() > today_date],
            key=lambda a: a.due_date,
        )[:5]

        recent_grades = (
            Submission.query.filter_by(student_id=current_user.id)
            .filter(Submission.score.isnot(None))
            .order_by(Submission.graded_at.desc())
            .limit(5)
            .all()
        )

    return render_template(
        "student/dashboard.html",
        classes=classes,
        today_timetable=today_timetable,
        due_today=due_today,
        upcoming_homework=upcoming_homework,
        recent_grades=recent_grades,
    )


@student_bp.route("/timetable")
@login_required
@role_required("student")
def timetable_view():
    class_ids = [
        e.class_group_id
        for e in Enrollment.query.filter_by(student_id=current_user.id).all()
    ]
    periods, grid = build_week_grid(class_ids)
    return render_template(
        "student/timetable.html", periods=periods, grid=grid, day_names=DAY_NAMES
    )
