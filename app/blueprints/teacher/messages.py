from flask import render_template, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.models.message import Conversation
from app.models.assignment import Assignment
from app.models.group_collab import ProjectGroup
from app.services import messaging_service


@teacher_bp.route("/messages")
@login_required
@role_required("teacher")
def messages_list():
    conversations = (
        Conversation.query.filter_by(teacher_id=current_user.id)
        .order_by(Conversation.last_message_at.is_(None), Conversation.last_message_at.desc())
        .all()
    )
    conversed_student_ids = {c.student_id for c in conversations}
    students = messaging_service.get_teacher_students(current_user.id)
    new_contacts = [s for s in students if s.id not in conversed_student_ids]

    rows = []
    for c in conversations:
        unread = sum(1 for m in c.messages if not m.is_read and m.sender_id != current_user.id)
        rows.append({"conversation": c, "student": c.student, "unread": unread})

    assignment_ids = [
        a.id for a in Assignment.query.filter_by(teacher_id=current_user.id).all()
    ]
    group_links = []
    if assignment_ids:
        groups = ProjectGroup.query.filter(ProjectGroup.assignment_id.in_(assignment_ids)).all()
        group_links = [{"assignment": g.assignment, "group": g} for g in groups]

    return render_template(
        "teacher/messages_list.html", rows=rows, new_contacts=new_contacts, group_links=group_links
    )


@teacher_bp.route("/messages/<int:student_id>")
@login_required
@role_required("teacher")
def message_thread(student_id):
    conversation = messaging_service.get_or_create_conversation(student_id, current_user.id)
    if conversation is None:
        abort(404, description="You can only message students in your own classes.")
    return render_template(
        "teacher/message_thread.html", conversation=conversation, other_party=conversation.student
    )
