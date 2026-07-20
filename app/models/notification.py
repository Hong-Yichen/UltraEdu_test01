from datetime import datetime, timezone

from app.constants import ANNOUNCEMENT_TYPES, NOTIFICATION_TYPES
from app.extensions import db


class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    class_group_id = db.Column(db.Integer, db.ForeignKey("class_groups.id"), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    announcement_type = db.Column(db.String(30), nullable=False, default="general")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    published_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    teacher = db.relationship("User")
    class_group = db.relationship("ClassGroup")
    subject = db.relationship("Subject")

    __table_args__ = (
        db.CheckConstraint(announcement_type.in_(ANNOUNCEMENT_TYPES), name="ck_announcement_type"),
    )


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(30), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text)
    link_url = db.Column(db.String(500))
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    related_object_type = db.Column(db.String(40))
    related_object_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    user = db.relationship("User")

    __table_args__ = (
        db.CheckConstraint(type.in_(NOTIFICATION_TYPES), name="ck_notification_type"),
    )
