from flask import render_template, abort
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.models.message import Conversation
from app.models.group_collab import ProjectGroupMembership
from app.services import messaging_service


@student_bp.route("/messages")
@login_required
@role_required("student")
def messages_list():
    teachers = messaging_service.get_student_teachers(current_user.id)
    conversations = {
        c.teacher_id: c
        for c in Conversation.query.filter_by(student_id=current_user.id).all()
    }
    rows = []
    for teacher in teachers:
        conversation = conversations.get(teacher.id)
        unread = 0
        if conversation:
            unread = sum(1 for m in conversation.messages if not m.is_read and m.sender_id != current_user.id)
        rows.append({"teacher": teacher, "conversation": conversation, "unread": unread})

    memberships = ProjectGroupMembership.query.filter_by(student_id=current_user.id).all()
    group_links = [
        {"assignment": m.group.assignment, "group": m.group}
        for m in memberships
    ]

    return render_template("student/messages_list.html", rows=rows, group_links=group_links)


@student_bp.route("/messages/<int:teacher_id>")
@login_required
@role_required("student")
def message_thread(teacher_id):
    conversation = messaging_service.get_or_create_conversation(current_user.id, teacher_id)
    if conversation is None:
        abort(404, description="You can only message teachers of your own classes.")
    return render_template(
        "student/message_thread.html", conversation=conversation, other_party=conversation.teacher
    )
