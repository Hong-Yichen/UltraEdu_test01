from datetime import datetime, timezone

from app.extensions import db


class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=True)
    storybook_id = db.Column(db.Integer, db.ForeignKey("storybooks.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    subject = db.relationship("Subject")
    assignment = db.relationship("Assignment")
    resource = db.relationship("Resource")
    storybook = db.relationship("Storybook")
