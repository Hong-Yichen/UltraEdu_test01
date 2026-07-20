from flask import render_template
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.models.academic import Enrollment
from app.models.assignment import Assignment, Submission


@student_bp.route("/examinations")
@login_required
@role_required("student")
def examinations_list():
    class_ids = [
        e.class_group_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()
    ]
    examinations = []
    if class_ids:
        examinations = (
            Assignment.query.filter(
                Assignment.class_group_id.in_(class_ids),
                Assignment.published_at.isnot(None),
                Assignment.is_exam.is_(True),
            )
            .order_by(Assignment.due_date.is_(None), Assignment.due_date)
            .all()
        )
    submission_by_assignment = {
        s.assignment_id: s
        for s in Submission.query.filter_by(student_id=current_user.id).all()
    }
    return render_template(
        "student/examinations_list.html",
        examinations=examinations,
        submission_by_assignment=submission_by_assignment,
    )
