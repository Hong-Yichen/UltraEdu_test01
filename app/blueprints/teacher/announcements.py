from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.constants import ANNOUNCEMENT_TYPES
from app.extensions import db
from app.models.academic import ClassGroup, Enrollment
from app.models.notification import Announcement
from app.services.notifications_service import notify_class


@teacher_bp.route("/announcements")
@login_required
@role_required("teacher")
def announcements_list():
    announcements = (
        Announcement.query.filter_by(teacher_id=current_user.id)
        .order_by(Announcement.created_at.desc())
        .all()
    )
    return render_template("teacher/announcements_list.html", announcements=announcements)


@teacher_bp.route("/announcements/new", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def announcements_new():
    classes = ClassGroup.query.filter_by(teacher_id=current_user.id).order_by(ClassGroup.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        announcement_type = request.form.get("announcement_type", "general")
        class_group_id = request.form.get("class_group_id", type=int) or None

        errors = []
        if not title:
            errors.append("Title is required.")
        if not body:
            errors.append("Message is required.")
        if announcement_type not in ANNOUNCEMENT_TYPES:
            errors.append("Choose a valid announcement type.")
        class_group = None
        if class_group_id:
            class_group = ClassGroup.query.filter_by(
                id=class_group_id, teacher_id=current_user.id
            ).first()
            if class_group is None:
                errors.append("Invalid class.")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            announcement = Announcement(
                teacher_id=current_user.id,
                class_group_id=class_group.id if class_group else None,
                subject_id=class_group.subject_id if class_group else None,
                title=title,
                body=body,
                announcement_type=announcement_type,
            )
            db.session.add(announcement)

            if class_group:
                student_ids = [
                    e.student_id
                    for e in Enrollment.query.filter_by(class_group_id=class_group.id).all()
                ]
                notify_class(
                    student_ids,
                    "announcement",
                    title,
                    body,
                    related_object_type="announcement",
                )

            db.session.commit()
            flash("Announcement posted.", "success")
            return redirect(url_for("teacher.announcements_list"))

    return render_template(
        "teacher/announcements_new.html", classes=classes, announcement_types=ANNOUNCEMENT_TYPES
    )
