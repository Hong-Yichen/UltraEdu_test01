from flask import jsonify, request, abort
from flask_login import login_required, current_user

from app.blueprints.api import api_bp
from app.extensions import db
from app.models.message import Conversation, Message
from app.services import messaging_service
from app.services.exam_lockdown_guard import get_active_exam_session


def _get_participant_conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    if current_user.id not in (conversation.student_id, conversation.teacher_id):
        abort(404)
    if current_user.is_student and get_active_exam_session(current_user) is not None:
        abort(403, description="Messaging is disabled during an exam.")
    return conversation


def _serialize_message(message):
    return {
        "id": message.id,
        "sender_id": message.sender_id,
        "sender_name": message.sender.full_name,
        "body": message.body,
        "is_read": message.is_read,
        "created_at": message.created_at.isoformat(),
    }


@api_bp.route("/conversations/<int:conversation_id>/messages")
@login_required
def list_conversation_messages(conversation_id):
    conversation = _get_participant_conversation(conversation_id)
    unread = Message.query.filter(
        Message.conversation_id == conversation.id,
        Message.sender_id != current_user.id,
        Message.is_read.is_(False),
    ).all()
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()
    return jsonify(
        {
            "messages": [_serialize_message(m) for m in conversation.messages],
            "other_party_name": conversation.other_party(current_user.id).full_name,
        }
    )


@api_bp.route("/conversations/<int:conversation_id>/messages", methods=["POST"])
@login_required
def post_conversation_message(conversation_id):
    conversation = _get_participant_conversation(conversation_id)
    data = request.get_json(force=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        abort(400, description="Message cannot be empty.")
    message = messaging_service.send_message(conversation, current_user.id, body)

    from app.services.notifications_service import create_notification

    recipient_id = conversation.teacher_id if current_user.id == conversation.student_id else conversation.student_id
    create_notification(
        recipient_id, "new_message", f"New message from {current_user.full_name}",
        body[:140], related_object_type="conversation", related_object_id=conversation.id,
    )
    db.session.commit()

    return jsonify(_serialize_message(message)), 201


@api_bp.route("/conversations/unread-count")
@login_required
def unread_conversation_count():
    return jsonify({"unread_count": messaging_service.unread_count_for(current_user.id)})
