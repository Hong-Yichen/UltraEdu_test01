from datetime import datetime, timezone

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.constants import DIFFICULTIES
from app.extensions import db
from app.models.academic import ClassGroup, Enrollment
from app.models.worksheet import Worksheet
from app.models.assignment import Assignment, Submission
from app.models.exam_lockdown import ExamSession
from app.services.notifications_service import notify_class


def _get_owned_examination(assignment_id):
    assignment = Assignment.query.filter_by(
        id=assignment_id, teacher_id=current_user.id, is_exam=True
    ).first()
    if assignment is None:
        abort(404)
    return assignment


@teacher_bp.route("/examinations")
@login_required
@role_required("teacher")
def examinations_list():
    examinations = (
        Assignment.query.filter_by(teacher_id=current_user.id, is_exam=True)
        .order_by(Assignment.created_at.desc())
        .all()
    )
    return render_template("teacher/examinations_list.html", examinations=examinations)


@teacher_bp.route("/examinations/new", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def examinations_new():
    classes = ClassGroup.query.filter_by(teacher_id=current_user.id).order_by(ClassGroup.name).all()
    worksheets = Worksheet.query.filter_by(teacher_id=current_user.id).order_by(Worksheet.title).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        class_group_id = request.form.get("class_group_id", type=int)
        worksheet_id = request.form.get("worksheet_id", type=int) or None
        difficulty = request.form.get("difficulty", "medium")
        due_date_raw = request.form.get("due_date", "")
        max_score = request.form.get("max_score", type=int) or 10
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
            examination = Assignment(
                title=title,
                description=description or None,
                class_group_id=class_group.id,
                teacher_id=current_user.id,
                subject_id=class_group.subject_id,
                assignment_type="worksheet" if worksheet else "file_upload",
                worksheet_id=worksheet.id if worksheet else None,
                difficulty=difficulty,
                ai_mode="disabled",  # AI hints are never available during an examination
                is_exam=True,
                max_score=max_score,
                due_date=due_date,
            )
            db.session.add(examination)
            db.session.commit()
            flash(
                "Examination created as a draft. Publish it when you're ready — "
                "Exam Mode turns on automatically and AI hints stay off.",
                "success",
            )
            return redirect(url_for("teacher.examination_detail", assignment_id=examination.id))

    return render_template(
        "teacher/examinations_new.html",
        classes=classes,
        worksheets=worksheets,
        difficulties=DIFFICULTIES,
    )


@teacher_bp.route("/examinations/<int:assignment_id>")
@login_required
@role_required("teacher")
def examination_detail(assignment_id):
    examination = _get_owned_examination(assignment_id)
    submissions = Submission.query.filter_by(assignment_id=examination.id).all()
    status_order = {"submitted": 0, "graded": 1, "returned": 1, "in_progress": 2, "not_started": 3}
    submissions.sort(
        key=lambda s: (
            status_order.get(s.status, 4),
            -(s.submitted_at.timestamp() if s.submitted_at else 0),
        )
    )
    total_students = Enrollment.query.filter_by(class_group_id=examination.class_group_id).count()
    active_session = ExamSession.query.filter_by(assignment_id=examination.id, is_active=True).first()
    return render_template(
        "teacher/examination_detail.html",
        examination=examination,
        submissions=submissions,
        total_students=total_students,
        exam_is_active=active_session is not None,
    )


@teacher_bp.route("/examinations/<int:assignment_id>/publish", methods=["POST"])
@login_required
@role_required("teacher")
def examination_publish(assignment_id):
    examination = _get_owned_examination(assignment_id)
    if not examination.is_published:
        examination.published_at = datetime.utcnow()

        student_ids = [
            e.student_id
            for e in Enrollment.query.filter_by(class_group_id=examination.class_group_id).all()
        ]
        notify_class(
            student_ids,
            "new_assignment",
            f"Examination: {examination.title}",
            examination.description,
            link_url=url_for("student.assignment_detail", assignment_id=examination.id),
            related_object_type="assignment",
            related_object_id=examination.id,
        )

        # Publishing an examination automatically turns on Exam Mode for the class —
        # no separate manual toggle. Mirrors teacher.exam_activate's logic.
        ExamSession.query.filter_by(assignment_id=examination.id, is_active=True).update(
            {"is_active": False, "ended_at": datetime.now(timezone.utc)}
        )
        for student_id in student_ids:
            db.session.add(
                ExamSession(
                    student_id=student_id,
                    assignment_id=examination.id,
                    class_group_id=examination.class_group_id,
                    activated_by=current_user.id,
                )
            )
        examination.exam_mode_enabled = True
        db.session.commit()
        flash("Examination published — Exam Mode is now active for this class.", "success")
    return redirect(url_for("teacher.examination_detail", assignment_id=examination.id))


@teacher_bp.route("/examinations/<int:assignment_id>/end", methods=["POST"])
@login_required
@role_required("teacher")
def examination_end(assignment_id):
    examination = _get_owned_examination(assignment_id)
    ExamSession.query.filter_by(assignment_id=examination.id, is_active=True).update(
        {"is_active": False, "ended_at": datetime.now(timezone.utc)}
    )
    examination.exam_mode_enabled = False
    db.session.commit()
    flash("Examination ended — students have normal access again.", "success")
    return redirect(url_for("teacher.examination_detail", assignment_id=examination.id))
