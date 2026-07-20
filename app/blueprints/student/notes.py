from flask import render_template
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.models.academic import Enrollment
from app.models.resource import Resource
from app.models.notification import Announcement


@student_bp.route("/notes")
@login_required
@role_required("student")
def notes_list():
    subject_ids = _enrolled_subject_ids(current_user.id)
    resources = (
        Resource.query.filter(Resource.subject_id.in_(subject_ids))
        .order_by(Resource.created_at.desc())
        .all()
        if subject_ids
        else []
    )
    return render_template("student/notes_list.html", resources=resources)


@student_bp.route("/announcements")
@login_required
@role_required("student")
def announcements_list():
    class_ids = [
        e.class_group_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()
    ]
    announcements = []
    if class_ids:
        announcements = (
            Announcement.query.filter(
                (Announcement.class_group_id.in_(class_ids))
                | (Announcement.class_group_id.is_(None))
            )
            .order_by(Announcement.created_at.desc())
            .all()
        )
    return render_template("student/announcements_list.html", announcements=announcements)


def _enrolled_subject_ids(student_id):
    from app.models.academic import ClassGroup

    class_ids = [e.class_group_id for e in Enrollment.query.filter_by(student_id=student_id).all()]
    if not class_ids:
        return []
    return [
        c.subject_id for c in ClassGroup.query.filter(ClassGroup.id.in_(class_ids)).all()
    ]
