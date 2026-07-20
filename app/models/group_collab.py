from datetime import datetime, timezone

from app.extensions import db


class ProjectGroup(db.Model):
    __tablename__ = "project_groups"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    assignment = db.relationship("Assignment")
    memberships = db.relationship(
        "ProjectGroupMembership", backref="group", cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "GroupComment", backref="group", cascade="all, delete-orphan",
        order_by="GroupComment.created_at",
    )
    files = db.relationship(
        "GroupFile", backref="group", cascade="all, delete-orphan",
        order_by="GroupFile.uploaded_at",
    )
    document = db.relationship(
        "GroupDocument", backref="group", uselist=False, cascade="all, delete-orphan"
    )
    messages = db.relationship(
        "GroupMessage", backref="group", cascade="all, delete-orphan",
        order_by="GroupMessage.created_at",
    )

    @property
    def student_ids(self):
        return [m.student_id for m in self.memberships]


class ProjectGroupMembership(db.Model):
    __tablename__ = "project_group_memberships"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("project_groups.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_leader = db.Column(db.Boolean, nullable=False, default=False)

    student = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("group_id", "student_id", name="uq_group_membership"),
    )


class GroupComment(db.Model):
    __tablename__ = "group_comments"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("project_groups.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    student = db.relationship("User")


class GroupFile(db.Model):
    __tablename__ = "group_files"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("project_groups.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    student = db.relationship("User")


class GroupDocument(db.Model):
    """A single shared, co-editable text document per project group."""

    __tablename__ = "group_documents"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("project_groups.id"), nullable=False, unique=True)
    title = db.Column(db.String(200), nullable=False, default="Shared Document")
    content = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    updated_by = db.relationship("User")
    revisions = db.relationship(
        "GroupDocumentRevision", backref="document", cascade="all, delete-orphan",
        order_by="GroupDocumentRevision.created_at.desc()",
    )


class GroupDocumentRevision(db.Model):
    """One saved snapshot of a GroupDocument — the document's edit history."""

    __tablename__ = "group_document_revisions"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("group_documents.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    student = db.relationship("User")


class GroupMessage(db.Model):
    """Teammate-to-teammate chat scoped to a single project group."""

    __tablename__ = "group_messages"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("project_groups.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    student = db.relationship("User")
