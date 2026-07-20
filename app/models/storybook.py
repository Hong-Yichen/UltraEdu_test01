from datetime import datetime, timezone

from app.constants import STORYBOOK_LANGUAGES, AI_MODES
from app.extensions import db


class Storybook(db.Model):
    __tablename__ = "storybooks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(20), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    cover_image_path = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text)
    worksheet_id = db.Column(db.Integer, db.ForeignKey("worksheets.id"), nullable=True)
    ai_mode = db.Column(db.String(20), nullable=False, default="disabled")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    subject = db.relationship("Subject")
    worksheet = db.relationship("Worksheet")
    pages = db.relationship(
        "StorybookPage", backref="storybook", cascade="all, delete-orphan",
        order_by="StorybookPage.page_number",
    )

    __table_args__ = (
        db.CheckConstraint(language.in_(STORYBOOK_LANGUAGES), name="ck_storybook_language"),
        db.CheckConstraint(ai_mode.in_(AI_MODES), name="ck_storybook_ai_mode"),
    )


class StorybookPage(db.Model):
    __tablename__ = "storybook_pages"

    id = db.Column(db.Integer, primary_key=True)
    storybook_id = db.Column(db.Integer, db.ForeignKey("storybooks.id"), nullable=False)
    page_number = db.Column(db.Integer, nullable=False, default=1)
    text_content = db.Column(db.Text, nullable=False, default="")
    image_path = db.Column(db.String(500), nullable=True)
    audio_path = db.Column(db.String(500), nullable=True)
