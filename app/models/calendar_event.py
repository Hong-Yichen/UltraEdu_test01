from datetime import datetime, timezone

from app.constants import CALENDAR_EVENT_TYPES
from app.extensions import db


class CalendarEvent(db.Model):
    __tablename__ = "calendar_events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(20), nullable=False, default="school_event")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    class_group_id = db.Column(db.Integer, db.ForeignKey("class_groups.id"), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    class_group = db.relationship("ClassGroup")
    subject = db.relationship("Subject")
    creator = db.relationship("User")

    __table_args__ = (
        db.CheckConstraint(event_type.in_(CALENDAR_EVENT_TYPES), name="ck_calendar_event_type"),
    )

    @property
    def is_school_wide(self):
        return self.class_group_id is None
