from datetime import datetime, timezone

from app.constants import WORKSHEET_ELEMENT_TYPES
from app.extensions import db


class Worksheet(db.Model):
    __tablename__ = "worksheets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    description = db.Column(db.Text)
    page_width = db.Column(db.Integer, nullable=False, default=794)
    page_height = db.Column(db.Integer, nullable=False, default=1123)
    is_template = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    teacher = db.relationship("User")
    subject = db.relationship("Subject")
    elements = db.relationship(
        "WorksheetElement",
        backref="worksheet",
        cascade="all, delete-orphan",
        order_by="WorksheetElement.order_index",
    )

    @property
    def page_count(self):
        if not self.elements:
            return 1
        return max(e.page_number for e in self.elements)


class WorksheetElement(db.Model):
    __tablename__ = "worksheet_elements"

    id = db.Column(db.Integer, primary_key=True)
    worksheet_id = db.Column(db.Integer, db.ForeignKey("worksheets.id"), nullable=False)
    element_type = db.Column(db.String(30), nullable=False)
    page_number = db.Column(db.Integer, nullable=False, default=1)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    x = db.Column(db.Float, nullable=False, default=40)
    y = db.Column(db.Float, nullable=False, default=40)
    width = db.Column(db.Float, nullable=False, default=300)
    height = db.Column(db.Float, nullable=False, default=100)
    prompt_text = db.Column(db.Text)
    points = db.Column(db.Integer, nullable=False, default=1)
    config_json = db.Column(db.JSON, nullable=False, default=dict)

    __table_args__ = (
        db.CheckConstraint(element_type.in_(WORKSHEET_ELEMENT_TYPES), name="ck_element_type"),
    )
