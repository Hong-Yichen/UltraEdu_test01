from datetime import datetime

from flask import jsonify, request, abort
from flask_login import login_required, current_user

from app.blueprints.api import api_bp
from app.extensions import db
from app.models.group_collab import ProjectGroup, ProjectGroupMembership, GroupMessage
from app.services.exam_lockdown_guard import get_active_exam_session


def _get_authorized_group(group_id):
    group = ProjectGroup.query.get_or_404(group_id)
    if current_user.is_teacher:
        if group.assignment.teacher_id != current_user.id:
            abort(404)
        return group
    if current_user.is_student:
        membership = ProjectGroupMembership.query.filter_by(
            group_id=group_id, student_id=current_user.id
        ).first()
        if membership is None:
            abort(404)
        if get_active_exam_session(current_user) is not None:
            abort(403, description="Group messaging is disabled during an exam.")
        return group
    abort(404)


def _chat_closed(group):
    due_date = group.assignment.due_date
    return due_date is not None and datetime.utcnow() > due_date


def _serialize_message(message):
    return {
        "id": message.id,
        "student_id": message.student_id,
        "sender_name": message.student.full_name,
        "is_teacher": message.student.is_teacher,
        "body": message.body,
        "created_at": message.created_at.isoformat(),
    }


@api_bp.route("/groups/<int:group_id>/messages")
@login_required
def list_group_messages(group_id):
    group = _get_authorized_group(group_id)
    return jsonify(
        {
            "messages": [_serialize_message(m) for m in group.messages],
            "chat_closed": _chat_closed(group),
        }
    )


@api_bp.route("/groups/<int:group_id>/messages", methods=["POST"])
@login_required
def post_group_message(group_id):
    group = _get_authorized_group(group_id)
    if _chat_closed(group):
        abort(403, description="Team chat is closed — the assignment's due date has passed.")
    data = request.get_json(force=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        abort(400, description="Message cannot be empty.")
    message = GroupMessage(group_id=group.id, student_id=current_user.id, body=body)
    db.session.add(message)
    db.session.commit()
    return jsonify(_serialize_message(message)), 201
