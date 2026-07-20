from flask import render_template
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.models.academic import Enrollment, ClassGroup
from app.models.assignment import Assignment, Submission


@student_bp.route("/progress")
@login_required
@role_required("student")
def progress():
    class_ids = [e.class_group_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()]
    assignments = []
    if class_ids:
        assignments = Assignment.query.filter(
            Assignment.class_group_id.in_(class_ids), Assignment.published_at.isnot(None)
        ).all()
    assignment_ids = [a.id for a in assignments]

    submissions = []
    if assignment_ids:
        submissions = Submission.query.filter(
            Submission.assignment_id.in_(assignment_ids), Submission.student_id == current_user.id
        ).all()
    submission_by_assignment = {s.assignment_id: s for s in submissions}

    completed = [
        s for s in submissions if s.status in ("submitted", "graded", "returned", "needs_revision")
    ]
    pending = [a for a in assignments if a.id not in submission_by_assignment or submission_by_assignment[a.id].status == "in_progress"]
    graded = [s for s in submissions if s.score is not None and s.max_score]
    overall_pct = None
    if graded:
        overall_pct = round(sum((s.score / s.max_score) * 100 for s in graded) / len(graded), 1)

    subject_progress = {}
    for a in assignments:
        entry = subject_progress.setdefault(a.subject.name, {"total": 0, "completed": 0})
        entry["total"] += 1
        sub = submission_by_assignment.get(a.id)
        if sub and sub.status in ("submitted", "graded", "returned"):
            entry["completed"] += 1

    upcoming = sorted(
        [a for a in assignments if a.id not in submission_by_assignment and a.due_date],
        key=lambda a: a.due_date,
    )[:5]

    return render_template(
        "student/progress.html",
        overall_pct=overall_pct,
        completed_count=len(completed),
        pending_count=len(pending),
        subject_progress=subject_progress,
        upcoming=upcoming,
    )
