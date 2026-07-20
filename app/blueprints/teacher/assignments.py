from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.constants import DIFFICULTIES, AI_MODES
from app.extensions import db
from app.models.academic import ClassGroup, Enrollment
from app.models.worksheet import Worksheet
from app.models.assignment import Assignment, Submission
from app.services.notifications_service import notify_class


def _get_owned_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, teacher_id=current_user.id).first()
    if assignment is None:
        abort(404)
    return assignment


@teacher_bp.route("/assignments")
@login_required
@role_required("teacher")
def assignments_list():
    assignments = (
        Assignment.query.filter_by(teacher_id=current_user.id, is_exam=False)
        .order_by(Assignment.created_at.desc())
        .all()
    )
    return render_template("teacher/assignments_list.html", assignments=assignments)


@teacher_bp.route("/assignments/new", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def assignments_new():
    classes = ClassGroup.query.filter_by(teacher_id=current_user.id).order_by(ClassGroup.name).all()
    worksheets = Worksheet.query.filter_by(teacher_id=current_user.id).order_by(Worksheet.title).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        class_group_id = request.form.get("class_group_id", type=int)
        worksheet_id = request.form.get("worksheet_id", type=int) or None
        difficulty = request.form.get("difficulty", "medium")
        ai_mode = request.form.get("ai_mode", "disabled")
        due_date_raw = request.form.get("due_date", "")
        max_score = request.form.get("max_score", type=int) or 10
        allow_image_upload = request.form.get("allow_image_upload") == "on"
        allow_file_attachment = request.form.get("allow_file_attachment") == "on"
        is_group_assignment = request.form.get("is_group_assignment") == "on"
        description = request.form.get("description", "").strip()

        class_group = ClassGroup.query.filter_by(
            id=class_group_id, teacher_id=current_user.id
        ).first()

        errors = []
        if not title:
            errors.append("Title is required.")
        if class_group is None:
            errors.append("Choose a class.")
        if difficulty not in DIFFICULTIES:
            errors.append("Invalid difficulty.")
        if ai_mode not in AI_MODES:
            errors.append("Invalid AI mode.")
        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.fromisoformat(due_date_raw)
            except ValueError:
                errors.append("Invalid due date.")
        worksheet = None
        if worksheet_id:
            worksheet = Worksheet.query.filter_by(
                id=worksheet_id, teacher_id=current_user.id
            ).first()
            if worksheet is None:
                errors.append("Invalid worksheet.")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            assignment = Assignment(
                title=title,
                description=description or None,
                class_group_id=class_group.id,
                teacher_id=current_user.id,
                subject_id=class_group.subject_id,
                assignment_type="worksheet" if worksheet else "file_upload",
                worksheet_id=worksheet.id if worksheet else None,
                difficulty=difficulty,
                ai_mode=ai_mode,
                allow_image_upload=allow_image_upload,
                allow_file_attachment=allow_file_attachment,
                is_group_assignment=is_group_assignment,
                max_score=max_score,
                due_date=due_date,
            )
            db.session.add(assignment)
            db.session.commit()
            flash("Assignment created as a draft. Publish it to notify students.", "success")
            if is_group_assignment:
                return redirect(url_for("teacher.assignment_groups", assignment_id=assignment.id))
            return redirect(url_for("teacher.assignment_detail", assignment_id=assignment.id))

    return render_template(
        "teacher/assignments_new.html",
        classes=classes,
        worksheets=worksheets,
        difficulties=DIFFICULTIES,
        ai_modes=AI_MODES,
    )


@teacher_bp.route("/assignments/<int:assignment_id>")
@login_required
@role_required("teacher")
def assignment_detail(assignment_id):
    assignment = _get_owned_assignment(assignment_id)
    submissions = Submission.query.filter_by(assignment_id=assignment.id).all()
    # Surface work that needs grading first, then graded/returned, then in-progress.
    status_order = {"submitted": 0, "graded": 1, "returned": 1, "in_progress": 2, "not_started": 3}
    submissions.sort(
        key=lambda s: (
            status_order.get(s.status, 4),
            -(s.submitted_at.timestamp() if s.submitted_at else 0),
        )
    )
    total_students = Enrollment.query.filter_by(class_group_id=assignment.class_group_id).count()
    return render_template(
        "teacher/assignment_detail.html",
        assignment=assignment,
        submissions=submissions,
        total_students=total_students,
    )


@teacher_bp.route("/assignments/<int:assignment_id>/publish", methods=["POST"])
@login_required
@role_required("teacher")
def assignment_publish(assignment_id):
    assignment = _get_owned_assignment(assignment_id)
    if not assignment.is_published:
        assignment.published_at = datetime.utcnow()
        student_ids = [
            e.student_id
            for e in Enrollment.query.filter_by(class_group_id=assignment.class_group_id).all()
        ]
        notify_class(
            student_ids,
            "new_assignment",
            f"New assignment: {assignment.title}",
            assignment.description,
            link_url=url_for("student.assignment_detail", assignment_id=assignment.id),
            related_object_type="assignment",
            related_object_id=assignment.id,
        )
        db.session.commit()
        flash("Assignment published.", "success")
    return redirect(url_for("teacher.assignment_detail", assignment_id=assignment.id))


@teacher_bp.route("/assignments/<int:assignment_id>/recall", methods=["POST"])
@login_required
@role_required("teacher")
def assignment_recall(assignment_id):
    assignment = _get_owned_assignment(assignment_id)
    if assignment.is_published:
        assignment.published_at = None
        db.session.commit()
        flash("Assignment recalled — it's hidden from students until you publish it again.", "success")
    return redirect(url_for("teacher.assignment_detail", assignment_id=assignment.id))
