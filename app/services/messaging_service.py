from datetime import datetime, timezone

from app.extensions import db
from app.models.academic import ClassGroup, Enrollment
from app.models.message import Conversation, Message


def get_student_teachers(student_id):
    """Distinct teachers of classes the student is enrolled in — the only people a
    student is allowed to message."""
    class_ids = [e.class_group_id for e in Enrollment.query.filter_by(student_id=student_id).all()]
    if not class_ids:
        return []
    classes = ClassGroup.query.filter(ClassGroup.id.in_(class_ids)).all()
    seen = {}
    for c in classes:
        seen[c.teacher_id] = c.teacher
    return list(seen.values())


def get_teacher_students(teacher_id):
    """Distinct students across all of this teacher's classes — the only people a
    teacher is allowed to message."""
    class_ids = [c.id for c in ClassGroup.query.filter_by(teacher_id=teacher_id).all()]
    if not class_ids:
        return []
    enrollments = Enrollment.query.filter(Enrollment.class_group_id.in_(class_ids)).all()
    seen = {}
    for e in enrollments:
        seen[e.student_id] = e.student
    return list(seen.values())


def can_message(student_id, teacher_id):
    return any(t.id == teacher_id for t in get_student_teachers(student_id))


def get_or_create_conversation(student_id, teacher_id):
    if not can_message(student_id, teacher_id):
        return None
    conversation = Conversation.query.filter_by(student_id=student_id, teacher_id=teacher_id).first()
    if conversation is None:
        conversation = Conversation(student_id=student_id, teacher_id=teacher_id)
        db.session.add(conversation)
        db.session.commit()
    return conversation


def send_message(conversation, sender_id, body):
    message = Message(conversation_id=conversation.id, sender_id=sender_id, body=body)
    conversation.last_message_at = datetime.now(timezone.utc)
    db.session.add(message)
    db.session.commit()
    return message


def unread_count_for(user_id):
    return (
        Message.query.join(Conversation)
        .filter(
            Message.is_read.is_(False),
            Message.sender_id != user_id,
            (Conversation.student_id == user_id) | (Conversation.teacher_id == user_id),
        )
        .count()
    )
