from datetime import datetime, timezone

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.extensions import db
from app.models.academic import Subject, ClassGroup, Enrollment
from app.models.textbook import Textbook
from app.services.file_storage import save_upload
from app.services.notifications_service import notify_class


def _get_owned_textbook(textbook_id):
    textbook = Textbook.query.filter_by(id=textbook_id, uploaded_by=current_user.id).first()
    if textbook is None:
        abort(404)
    return textbook


def _recipient_student_ids(textbook):
    if textbook.class_group_id:
        return [
            e.student_id
            for e in Enrollment.query.filter_by(class_group_id=textbook.class_group_id).all()
        ]
    class_ids = [
        c.id for c in ClassGroup.query.filter_by(
            teacher_id=textbook.uploaded_by, subject_id=textbook.subject_id
        ).all()
    ]
    if not class_ids:
        return []
    seen = set()
    for e in Enrollment.query.filter(Enrollment.class_group_id.in_(class_ids)).all():
        seen.add(e.student_id)
    return list(seen)


@teacher_bp.route("/textbooks")
@login_required
@role_required("teacher")
def textbooks_list():
    textbooks = (
        Textbook.query.filter_by(uploaded_by=current_user.id)
        .order_by(Textbook.created_at.desc())
        .all()
    )
    return render_template("teacher/textbooks_list.html", textbooks=textbooks)


@teacher_bp.route("/textbooks/new", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def textbooks_new():
    subjects = Subject.query.order_by(Subject.name).all()
    classes = ClassGroup.query.filter_by(teacher_id=current_user.id).order_by(ClassGroup.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject_id = request.form.get("subject_id", type=int)
        class_group_id = request.form.get("class_group_id", type=int) or None
        description = request.form.get("description", "").strip()
        upload = request.files.get("file")
        cover = request.files.get("cover_image")

        errors = []
        if not title:
            errors.append("Title is required.")
        subject = Subject.query.get(subject_id) if subject_id else None
        if subject is None:
            errors.append("Choose a subject.")
        if not upload or not upload.filename:
            errors.append("Choose a textbook file (PDF recommended) to upload.")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            file_path = save_upload(upload, subject.code)
            cover_image_path = save_upload(cover, subject.code) if cover and cover.filename else None
            textbook = Textbook(
                title=title,
                description=description or None,
                subject_id=subject.id,
                class_group_id=class_group_id,
                file_path=file_path,
                cover_image_path=cover_image_path,
                uploaded_by=current_user.id,
            )
            db.session.add(textbook)
            db.session.commit()
            flash("Textbook uploaded as a draft. Publish it so students can read it.", "success")
            return redirect(url_for("teacher.textbooks_list"))

    return render_template("teacher/textbooks_new.html", subjects=subjects, classes=classes)


@teacher_bp.route("/textbooks/<int:textbook_id>/publish", methods=["POST"])
@login_required
@role_required("teacher")
def textbook_publish(textbook_id):
    textbook = _get_owned_textbook(textbook_id)
    if not textbook.is_published:
        textbook.published_at = datetime.now(timezone.utc)
        student_ids = _recipient_student_ids(textbook)
        notify_class(
            student_ids,
            "new_textbook",
            f"New textbook: {textbook.title}",
            textbook.description,
            link_url=url_for("student.textbook_reader", textbook_id=textbook.id),
            related_object_type="textbook",
            related_object_id=textbook.id,
        )
        db.session.commit()
        flash("Textbook published — students can now read it.", "success")
    return redirect(url_for("teacher.textbooks_list"))


@teacher_bp.route("/textbooks/<int:textbook_id>/unpublish", methods=["POST"])
@login_required
@role_required("teacher")
def textbook_unpublish(textbook_id):
    textbook = _get_owned_textbook(textbook_id)
    textbook.published_at = None
    db.session.commit()
    flash("Textbook unpublished — hidden from students again.", "success")
    return redirect(url_for("teacher.textbooks_list"))


@teacher_bp.route("/textbooks/<int:textbook_id>/delete", methods=["POST"])
@login_required
@role_required("teacher")
def textbook_delete(textbook_id):
    textbook = _get_owned_textbook(textbook_id)
    db.session.delete(textbook)
    db.session.commit()
    flash("Textbook removed.", "success")
    return redirect(url_for("teacher.textbooks_list"))
