from datetime import datetime, timezone

from app.constants import RESOURCE_TYPES
from app.extensions import db


class Folder(db.Model):
    __tablename__ = "folders"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(40))
    parent_folder_id = db.Column(db.Integer, db.ForeignKey("folders.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    subject = db.relationship("Subject")
    children = db.relationship("Folder", backref=db.backref("parent", remote_side=[id]))


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey("folders.id"), nullable=True)
    resource_type = db.Column(db.String(30), nullable=False)
    class_group_id = db.Column(db.Integer, db.ForeignKey("class_groups.id"), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    subject = db.relationship("Subject")
    folder = db.relationship("Folder")
    class_group = db.relationship("ClassGroup")
    uploader = db.relationship("User")

    __table_args__ = (
        db.CheckConstraint(resource_type.in_(RESOURCE_TYPES), name="ck_resource_type"),
    )
