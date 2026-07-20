from datetime import datetime

from flask import render_template
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.constants import NON_ACADEMIC_SUBJECT_CODES
from app.models.academic import ClassGroup, Timetable, Subject
from app.models.assignment import Assignment, Submission
from app.models.notification import Announcement
from app.services.timetable_service import build_week_grid, DAY_NAMES


@teacher_bp.route("/dashboard")
@login_required
@role_required("teacher")
def dashboard():
    today_dow = datetime.now().weekday()
    all_classes = ClassGroup.query.filter_by(teacher_id=current_user.id).all()
    all_class_ids = [c.id for c in all_classes]
    # "Your Classes" excludes non-teaching timetable blocks (assembly/recess/dismissal);
    # today's timetable still includes them so the schedule reads correctly.
    classes = (
        ClassGroup.query.join(Subject, ClassGroup.subject_id == Subject.id)
        .filter(ClassGroup.teacher_id == current_user.id, Subject.code.notin_(NON_ACADEMIC_SUBJECT_CODES))
        .order_by(ClassGroup.name)
        .all()
    )
    today_timetable = []
    if all_class_ids:
        today_timetable = (
            Timetable.query.filter(
                Timetable.class_group_id.in_(all_class_ids), Timetable.day_of_week == today_dow
            )
            .order_by(Timetable.period_number)
            .all()
        )

    assignments = Assignment.query.filter_by(teacher_id=current_user.id).all()
    assignment_ids = [a.id for a in assignments]
    to_grade = []
    if assignment_ids:
        to_grade = Submission.query.filter(
            Submission.assignment_id.in_(assignment_ids), Submission.status == "submitted"
        ).all()

    recent_announcements = (
        Announcement.query.filter_by(teacher_id=current_user.id)
        .order_by(Announcement.created_at.desc())
        .limit(3)
        .all()
    )

    upcoming_exams = [
        a for a in assignments
        if a.is_exam and a.due_date and a.due_date >= datetime.utcnow()
    ]

    return render_template(
        "teacher/dashboard.html",
        classes=classes,
        today_timetable=today_timetable,
        to_grade=to_grade,
        recent_announcements=recent_announcements,
        upcoming_exams=upcoming_exams,
    )


@teacher_bp.route("/timetable")
@login_required
@role_required("teacher")
def timetable_view():
    all_class_ids = [c.id for c in ClassGroup.query.filter_by(teacher_id=current_user.id).all()]
    periods, grid = build_week_grid(all_class_ids)
    return render_template(
        "teacher/timetable.html", periods=periods, grid=grid, day_names=DAY_NAMES
    )
