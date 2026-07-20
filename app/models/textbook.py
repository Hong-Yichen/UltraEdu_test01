from datetime import datetime, timezone

from app.extensions import db


class Textbook(db.Model):
    __tablename__ = "textbooks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    class_group_id = db.Column(db.Integer, db.ForeignKey("class_groups.id"), nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    cover_image_path = db.Column(db.String(500), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    published_at = db.Column(db.DateTime, nullable=True)

    subject = db.relationship("Subject")
    class_group = db.relationship("ClassGroup")
    uploader = db.relationship("User")
    notes = db.relationship("TextbookNote", backref="textbook", cascade="all, delete-orphan")

    @property
    def is_published(self):
        return self.published_at is not None


class TextbookNote(db.Model):
    __tablename__ = "textbook_notes"

    id = db.Column(db.Integer, primary_key=True)
    textbook_id = db.Column(db.Integer, db.ForeignKey("textbooks.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    page_number = db.Column(db.Integer, nullable=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    student = db.relationship("User")


class TextbookPageAnnotation(db.Model):
    """Links a student's handwritten ink/highlight/shape/sticky-note overlay
    (a CanvasDocument) to one page of a textbook they're reading."""

    __tablename__ = "textbook_page_annotations"

    id = db.Column(db.Integer, primary_key=True)
    textbook_id = db.Column(db.Integer, db.ForeignKey("textbooks.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    canvas_document_id = db.Column(db.Integer, db.ForeignKey("canvas_documents.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    textbook = db.relationship("Textbook")
    student = db.relationship("User")
    canvas_document = db.relationship("CanvasDocument")

    __table_args__ = (
        db.UniqueConstraint(
            "textbook_id", "student_id", "page_number", name="uq_textbook_page_annotation"
        ),
    )
