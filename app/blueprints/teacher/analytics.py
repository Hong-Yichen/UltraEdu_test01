from flask import render_template, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.models.academic import ClassGroup, Enrollment
from app.models.assignment import Assignment, Submission


def _get_owned_class(class_group_id):
    class_group = ClassGroup.query.filter_by(id=class_group_id, teacher_id=current_user.id).first()
    if class_group is None:
        abort(404)
    return class_group


def _get_owned_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, teacher_id=current_user.id).first()
    if assignment is None:
        abort(404)
    return assignment


@teacher_bp.route("/analytics/class/<int:class_group_id>")
@login_required
@role_required("teacher")
def class_analytics(class_group_id):
    class_group = _get_owned_class(class_group_id)
    students = [e.student for e in Enrollment.query.filter_by(class_group_id=class_group.id).all()]
    assignments = Assignment.query.filter_by(class_group_id=class_group.id, teacher_id=current_user.id).all()
    assignment_ids = [a.id for a in assignments]

    graded_submissions = []
    if assignment_ids:
        graded_submissions = Submission.query.filter(
            Submission.assignment_id.in_(assignment_ids), Submission.score.isnot(None)
        ).all()

    class_average = None
    if graded_submissions:
        percentages = [
            (s.score / s.max_score) * 100 for s in graded_submissions if s.max_score
        ]
        class_average = round(sum(percentages) / len(percentages), 1) if percentages else None

    per_student = []
    for student in students:
        student_submissions = [s for s in graded_submissions if s.student_id == student.id]
        pct_list = [(s.score / s.max_score) * 100 for s in student_submissions if s.max_score]
        avg = round(sum(pct_list) / len(pct_list), 1) if pct_list else None
        total_assigned = len(assignments)
        total_submitted = Submission.query.filter(
            Submission.assignment_id.in_(assignment_ids), Submission.student_id == student.id,
            Submission.status.in_(_SUBMITTED_STATUSES),
        ).count() if assignment_ids else 0
        per_student.append(
            {
                "student": student,
                "average": avg,
                "completed": total_submitted,
                "total": total_assigned,
                "needs_support": avg is not None and avg < 60,
            }
        )

    completion_rate = None
    if assignments and students:
        expected = len(assignments) * len(students)
        actual = Submission.query.filter(
            Submission.assignment_id.in_(assignment_ids),
            Submission.status.in_(_SUBMITTED_STATUSES),
        ).count() if assignment_ids else 0
        completion_rate = round((actual / expected) * 100, 1) if expected else None

    return render_template(
        "teacher/class_analytics.html",
        class_group=class_group,
        class_average=class_average,
        completion_rate=completion_rate,
        per_student=per_student,
    )


_SUBMITTED_STATUSES = ("submitted", "graded", "returned", "needs_revision")


@teacher_bp.route("/analytics/assignment/<int:assignment_id>")
@login_required
@role_required("teacher")
def assignment_analytics(assignment_id):
    assignment = _get_owned_assignment(assignment_id)
    students = [
        e.student
        for e in Enrollment.query.filter_by(class_group_id=assignment.class_group_id).all()
    ]
    total_students = len(students)

    submissions = Submission.query.filter_by(assignment_id=assignment.id).all()
    submission_by_student = {s.student_id: s for s in submissions if s.student_id}

    submitted_count = len([s for s in submissions if s.status in _SUBMITTED_STATUSES])
    graded = [s for s in submissions if s.score is not None and s.max_score]
    average = None
    if graded:
        average = round(sum((s.score / s.max_score) * 100 for s in graded) / len(graded), 1)

    buckets = {"90-100": 0, "70-89": 0, "50-69": 0, "below 50": 0}
    for s in graded:
        pct = (s.score / s.max_score) * 100
        if pct >= 90:
            buckets["90-100"] += 1
        elif pct >= 70:
            buckets["70-89"] += 1
        elif pct >= 50:
            buckets["50-69"] += 1
        else:
            buckets["below 50"] += 1

    # Per-student breakdown: exactly who submitted, who didn't, and their grade.
    per_student = []
    for student in students:
        submission = submission_by_student.get(student.id)
        has_submitted = submission is not None and submission.status in _SUBMITTED_STATUSES
        per_student.append(
            {
                "student": student,
                "submission": submission,
                "has_submitted": has_submitted,
                "status": submission.status if submission else "not_started",
                "score": submission.score if submission else None,
                "max_score": submission.max_score if submission else assignment.max_score,
                "submitted_at": submission.submitted_at if submission else None,
            }
        )
    # Not-submitted first (needs follow-up), then ungraded submissions, then graded.
    status_priority = {
        "not_started": 0, "in_progress": 1, "submitted": 2,
        "graded": 3, "returned": 3, "needs_revision": 4,
    }
    per_student.sort(key=lambda row: status_priority.get(row["status"], 4))

    not_submitted_count = len([row for row in per_student if not row["has_submitted"]])

    return render_template(
        "teacher/assignment_analytics.html",
        assignment=assignment,
        total_students=total_students,
        submitted_count=submitted_count,
        not_submitted_count=not_submitted_count,
        average=average,
        buckets=buckets,
        per_student=per_student,
    )
