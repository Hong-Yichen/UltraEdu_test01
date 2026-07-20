from datetime import datetime, timezone

from app.constants import CANVAS_TOOLS
from app.extensions import db

CANVAS_OWNER_TYPES = (
    "student_answer",
    "annotation",
    "group_shared",
    "storybook_activity",
    "model_answer",
    "textbook_page",
)
CANVAS_LAYERS = ("base", "annotation")


class CanvasDocument(db.Model):
    __tablename__ = "canvas_documents"

    id = db.Column(db.Integer, primary_key=True)
    owner_type = db.Column(db.String(30), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    width = db.Column(db.Integer, nullable=False, default=800)
    height = db.Column(db.Integer, nullable=False, default=400)
    background_image_path = db.Column(db.String(500), nullable=True)
    is_locked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    creator = db.relationship("User")
    strokes = db.relationship(
        "CanvasStroke", backref="document", cascade="all, delete-orphan", order_by="CanvasStroke.sequence"
    )
    sticky_notes = db.relationship("StickyNote", backref="document", cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint(owner_type.in_(CANVAS_OWNER_TYPES), name="ck_canvas_owner_type"),
    )


class CanvasStroke(db.Model):
    __tablename__ = "canvas_strokes"

    id = db.Column(db.Integer, primary_key=True)
    canvas_document_id = db.Column(db.Integer, db.ForeignKey("canvas_documents.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    layer = db.Column(db.String(20), nullable=False, default="base")
    tool = db.Column(db.String(20), nullable=False, default="pen")
    color = db.Column(db.String(20), nullable=False, default="#1a1a1a")
    width = db.Column(db.Float, nullable=False, default=2.0)
    opacity = db.Column(db.Float, nullable=False, default=1.0)
    points_json = db.Column(db.JSON, nullable=False)
    sequence = db.Column(db.Integer, nullable=False, default=0)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    author = db.relationship("User")

    __table_args__ = (
        db.CheckConstraint(layer.in_(CANVAS_LAYERS), name="ck_stroke_layer"),
        db.CheckConstraint(tool.in_(CANVAS_TOOLS), name="ck_stroke_tool"),
    )


class StickyNote(db.Model):
    __tablename__ = "sticky_notes"

    id = db.Column(db.Integer, primary_key=True)
    canvas_document_id = db.Column(db.Integer, db.ForeignKey("canvas_documents.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False, default=160)
    height = db.Column(db.Float, nullable=False, default=120)
    text = db.Column(db.Text, nullable=False, default="")
    color = db.Column(db.String(20), nullable=False, default="#fff3b0")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    author = db.relationship("User")
