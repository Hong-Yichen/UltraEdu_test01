from datetime import datetime, timezone

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.extensions import db
from app.models.assignment import Assignment
from app.models.group_collab import (
    ProjectGroup,
    ProjectGroupMembership,
    GroupComment,
    GroupFile,
    GroupDocument,
    GroupDocumentRevision,
)
from app.services.file_storage import save_upload


def _get_my_group(assignment):
    membership = (
        ProjectGroupMembership.query.join(ProjectGroup)
        .filter(ProjectGroup.assignment_id == assignment.id, ProjectGroupMembership.student_id == current_user.id)
        .first()
    )
    if membership is None:
        abort(404, description="You're not in a group for this assignment yet.")
    return membership.group


@student_bp.route("/assignments/<int:assignment_id>/group")
@login_required
@role_required("student")
def group_workspace(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    group = _get_my_group(assignment)
    return render_template("student/group_workspace.html", assignment=assignment, group=group)


@student_bp.route("/assignments/<int:assignment_id>/group/document", methods=["POST"])
@login_required
@role_required("student")
def group_save_document(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    group = _get_my_group(assignment)
    content = request.form.get("content", "")

    document = group.document
    if document is None:
        document = GroupDocument(group_id=group.id, content=content, updated_by_id=current_user.id)
        db.session.add(document)
    else:
        document.content = content
        document.updated_by_id = current_user.id
        document.updated_at = datetime.now(timezone.utc)
    db.session.flush()
    db.session.add(
        GroupDocumentRevision(document_id=document.id, student_id=current_user.id, content=content)
    )
    db.session.commit()
    flash("Document saved.", "success")
    return redirect(url_for("student.group_workspace", assignment_id=assignment.id))


@student_bp.route("/assignments/<int:assignment_id>/group/comments", methods=["POST"])
@login_required
@role_required("student")
def group_add_comment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    group = _get_my_group(assignment)
    body = request.form.get("body", "").strip()
    if body:
        db.session.add(GroupComment(group_id=group.id, student_id=current_user.id, body=body))
        db.session.commit()
    return redirect(url_for("student.group_workspace", assignment_id=assignment.id))


@student_bp.route("/assignments/<int:assignment_id>/group/files", methods=["POST"])
@login_required
@role_required("student")
def group_add_file(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    group = _get_my_group(assignment)
    upload = request.files.get("file")
    if upload and upload.filename:
        file_path = save_upload(upload, assignment.subject.code)
        db.session.add(
            GroupFile(
                group_id=group.id, student_id=current_user.id,
                file_path=file_path, original_filename=upload.filename,
            )
        )
        db.session.commit()
        flash("File shared with your group.", "success")
    return redirect(url_for("student.group_workspace", assignment_id=assignment.id))
