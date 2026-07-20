from flask import send_from_directory, current_app, abort
from flask_login import login_required, current_user

from app.blueprints.api import api_bp
from app.services.exam_lockdown_guard import get_active_exam_session


def _allowed_during_exam(relative_path, exam_session):
    """During an active exam, a student may only fetch files that belong to that
    exam's own assignment (e.g. a teacher-attached exam paper) — not textbooks,
    storybooks, or other resources, even if they know/bookmarked the file URL."""
    from app.models.assignment import AssignmentAttachment

    return AssignmentAttachment.query.filter_by(
        assignment_id=exam_session.assignment_id, file_path=relative_path
    ).first() is not None


@api_bp.route("/uploads/<path:relative_path>")
@login_required
def serve_upload(relative_path):
    if ".." in relative_path:
        abort(404)
    if current_user.is_student:
        exam_session = get_active_exam_session(current_user)
        if exam_session is not None and not _allowed_during_exam(relative_path, exam_session):
            abort(403, description="This file isn't part of your current exam.")
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], relative_path)
