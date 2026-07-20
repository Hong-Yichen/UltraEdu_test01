from datetime import datetime, timezone

from app.constants import (
    ASSIGNMENT_TYPES,
    DIFFICULTIES,
    AI_MODES,
    SUBMISSION_STATUSES,
    SUBMISSION_NOT_STARTED,
)
from app.extensions import db


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    class_group_id = db.Column(db.Integer, db.ForeignKey("class_groups.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    assignment_type = db.Column(db.String(20), nullable=False, default="worksheet")
    worksheet_id = db.Column(db.Integer, db.ForeignKey("worksheets.id"), nullable=True)
    difficulty = db.Column(db.String(20), nullable=False, default="medium")
    ai_mode = db.Column(db.String(20), nullable=False, default="disabled")
    is_exam = db.Column(db.Boolean, nullable=False, default=False)
    exam_mode_enabled = db.Column(db.Boolean, nullable=False, default=False)
    is_group_assignment = db.Column(db.Boolean, nullable=False, default=False)
    allow_image_upload = db.Column(db.Boolean, nullable=False, default=False)
    allow_file_attachment = db.Column(db.Boolean, nullable=False, default=False)
    max_score = db.Column(db.Integer, nullable=False, default=10)
    due_date = db.Column(db.DateTime, nullable=True)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    class_group = db.relationship("ClassGroup")
    teacher = db.relationship("User")
    subject = db.relationship("Subject")
    worksheet = db.relationship("Worksheet")
    attachments = db.relationship(
        "AssignmentAttachment", backref="assignment", cascade="all, delete-orphan"
    )
    submissions = db.relationship(
        "Submission", backref="assignment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint(assignment_type.in_(ASSIGNMENT_TYPES), name="ck_assignment_type"),
        db.CheckConstraint(difficulty.in_(DIFFICULTIES), name="ck_assignment_difficulty"),
        db.CheckConstraint(ai_mode.in_(AI_MODES), name="ck_assignment_ai_mode"),
    )

    @property
    def is_published(self):
        return self.published_at is not None


class AssignmentAttachment(db.Model):
    __tablename__ = "assignment_attachments"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(80))
    uploaded_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=True)
    storybook_id = db.Column(db.Integer, db.ForeignKey("storybooks.id"), nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey("project_groups.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=SUBMISSION_NOT_STARTED)
    started_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    submitted_at = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Integer, nullable=True)
    max_score = db.Column(db.Integer, nullable=True)
    feedback_text = db.Column(db.Text)
    graded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)

    student = db.relationship("User", foreign_keys=[student_id])
    grader = db.relationship("User", foreign_keys=[graded_by])
    answers = db.relationship(
        "StudentAnswer", backref="submission", cascade="all, delete-orphan"
    )
    files = db.relationship(
        "SubmissionFile", backref="submission", cascade="all, delete-orphan"
    )
    voice_feedback = db.relationship(
        "VoiceFeedback", backref="submission", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint(status.in_(SUBMISSION_STATUSES), name="ck_submission_status"),
    )


class SubmissionFile(db.Model):
    __tablename__ = "submission_files"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class StudentAnswer(db.Model):
    __tablename__ = "student_answers"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    worksheet_element_id = db.Column(db.Integer, db.ForeignKey("worksheet_elements.id"), nullable=False)
    answer_json = db.Column(db.JSON, nullable=True)
    canvas_document_id = db.Column(db.Integer, db.ForeignKey("canvas_documents.id"), nullable=True)
    image_file_path = db.Column(db.String(500), nullable=True)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    worksheet_element = db.relationship("WorksheetElement")
    canvas_document = db.relationship("CanvasDocument")

    __table_args__ = (
        db.UniqueConstraint(
            "submission_id", "worksheet_element_id", name="uq_answer_submission_element"
        ),
    )


class ModelAnswer(db.Model):
    __tablename__ = "model_answers"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    worksheet_element_id = db.Column(db.Integer, db.ForeignKey("worksheet_elements.id"), nullable=True)
    canvas_document_id = db.Column(db.Integer, db.ForeignKey("canvas_documents.id"), nullable=True)
    text_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class VoiceFeedback(db.Model):
    """Stub only — no recording UI is built against this in the current build."""

    __tablename__ = "voice_feedback"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    audio_file_path = db.Column(db.String(500), nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    recorded_at = db.Column(db.DateTime, nullable=True)
