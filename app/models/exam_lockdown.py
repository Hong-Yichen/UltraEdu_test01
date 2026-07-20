from datetime import datetime, timezone

from app.extensions import db


class ExamSession(db.Model):
    __tablename__ = "exam_sessions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    class_group_id = db.Column(db.Integer, db.ForeignKey("class_groups.id"), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    activated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at = db.Column(db.DateTime, nullable=True)

    assignment = db.relationship("Assignment")


class LockdownSession(db.Model):
    __tablename__ = "lockdown_sessions"

    id = db.Column(db.Integer, primary_key=True)
    class_group_id = db.Column(db.Integer, db.ForeignKey("class_groups.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    allowed_resource_ids = db.Column(db.JSON, nullable=False, default=list)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    started_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at = db.Column(db.DateTime, nullable=True)

    class_group = db.relationship("ClassGroup")
    subject = db.relationship("Subject")
