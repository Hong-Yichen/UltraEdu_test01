from datetime import datetime, timezone

from app.extensions import db


class Conversation(db.Model):
    """A single 1:1 thread between one student and one teacher. There is no
    student-to-student or teacher-to-teacher messaging — every conversation has
    exactly one of each role, enforced in services/messaging_service.py."""

    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_message_at = db.Column(db.DateTime, nullable=True)

    student = db.relationship("User", foreign_keys=[student_id])
    teacher = db.relationship("User", foreign_keys=[teacher_id])
    messages = db.relationship(
        "Message", backref="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    __table_args__ = (
        db.UniqueConstraint("student_id", "teacher_id", name="uq_conversation_student_teacher"),
    )

    def other_party(self, user_id):
        return self.teacher if user_id == self.student_id else self.student


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    sender = db.relationship("User")
