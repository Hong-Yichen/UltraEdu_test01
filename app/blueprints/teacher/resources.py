from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.constants import RESOURCE_TYPES
from app.extensions import db
from app.models.academic import Subject, ClassGroup
from app.models.resource import Resource
from app.services.file_storage import save_upload


@teacher_bp.route("/resources")
@login_required
@role_required("teacher")
def resources_list():
    resources = (
        Resource.query.filter_by(uploaded_by=current_user.id)
        .order_by(Resource.created_at.desc())
        .all()
    )
    return render_template("teacher/resources_list.html", resources=resources)


@teacher_bp.route("/resources/new", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def resources_new():
    subjects = Subject.query.order_by(Subject.name).all()
    classes = ClassGroup.query.filter_by(teacher_id=current_user.id).order_by(ClassGroup.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject_id = request.form.get("subject_id", type=int)
        resource_type = request.form.get("resource_type")
        class_group_id = request.form.get("class_group_id", type=int) or None
        description = request.form.get("description", "").strip()
        upload = request.files.get("file")

        errors = []
        if not title:
            errors.append("Title is required.")
        subject = Subject.query.get(subject_id) if subject_id else None
        if subject is None:
            errors.append("Choose a subject.")
        if resource_type not in RESOURCE_TYPES:
            errors.append("Choose a valid resource type.")
        if not upload or not upload.filename:
            errors.append("Choose a file to upload.")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            file_path = save_upload(upload, subject.code)
            resource = Resource(
                title=title,
                description=description or None,
                subject_id=subject.id,
                resource_type=resource_type,
                class_group_id=class_group_id,
                file_path=file_path,
                uploaded_by=current_user.id,
            )
            db.session.add(resource)
            db.session.commit()
            flash("Resource uploaded.", "success")
            return redirect(url_for("teacher.resources_list"))

    return render_template(
        "teacher/resources_new.html",
        subjects=subjects,
        classes=classes,
        resource_types=RESOURCE_TYPES,
    )
