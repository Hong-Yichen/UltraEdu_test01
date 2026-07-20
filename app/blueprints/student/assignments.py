from datetime import datetime, timedelta, timezone

from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.constants import (
    CANVAS_ELEMENT_TYPES,
    SUBMISSION_IN_PROGRESS,
    SUBMISSION_SUBMITTED,
    SUBMISSION_NEEDS_REVISION,
)
from app.extensions import db
from app.models.academic import Enrollment
from app.models.assignment import Assignment, Submission, StudentAnswer
from app.services import canvas_service
from app.services.file_storage import save_upload
from app.services.notifications_service import create_notification


def _enrolled_class_ids(student_id):
    return [e.class_group_id for e in Enrollment.query.filter_by(student_id=student_id).all()]


def _get_visible_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.class_group_id not in _enrolled_class_ids(current_user.id):
        abort(404)
    if not assignment.is_published:
        abort(404)
    return assignment


def _get_or_create_submission(assignment):
    submission = Submission.query.filter_by(
        assignment_id=assignment.id, student_id=current_user.id
    ).first()
    if submission is None:
        submission = Submission(
            assignment_id=assignment.id,
            student_id=current_user.id,
            status=SUBMISSION_IN_PROGRESS,
            max_score=assignment.max_score,
        )
        db.session.add(submission)
        db.session.commit()
    return submission


@student_bp.route("/assignments")
@login_required
@role_required("student")
def assignments_list():
    class_ids = _enrolled_class_ids(current_user.id)
    assignments = []
    if class_ids:
        assignments = (
            Assignment.query.filter(
                Assignment.class_group_id.in_(class_ids),
                Assignment.published_at.isnot(None),
                Assignment.is_exam.is_(False),
            )
            .order_by(Assignment.due_date.is_(None), Assignment.due_date)
            .all()
        )
    submission_by_assignment = {
        s.assignment_id: s
        for s in Submission.query.filter_by(student_id=current_user.id).all()
    }
    return render_template(
        "student/assignments_list.html",
        assignments=assignments,
        submission_by_assignment=submission_by_assignment,
    )


@student_bp.route("/assignments/<int:assignment_id>")
@login_required
@role_required("student")
def assignment_detail(assignment_id):
    assignment = _get_visible_assignment(assignment_id)
    submission = _get_or_create_submission(assignment)

    answers_by_element = {a.worksheet_element_id: a for a in submission.answers}
    editable = submission.status in (SUBMISSION_IN_PROGRESS, SUBMISSION_NEEDS_REVISION)

    if assignment.worksheet_id and editable:
        for element in assignment.worksheet.elements:
            if element.element_type in CANVAS_ELEMENT_TYPES and element.id not in answers_by_element:
                document = canvas_service.create_document(
                    "student_answer", current_user.id, int(element.width), int(element.height)
                )
                answer = StudentAnswer(
                    submission_id=submission.id,
                    worksheet_element_id=element.id,
                    canvas_document_id=document.id,
                )
                db.session.add(answer)
                answers_by_element[element.id] = answer
        db.session.commit()

    from app.models.bookmark import Bookmark

    bookmark = Bookmark.query.filter_by(
        student_id=current_user.id, assignment_id=assignment.id
    ).first()

    return render_template(
        "student/assignment_take.html",
        assignment=assignment,
        submission=submission,
        answers_by_element=answers_by_element,
        readonly=not editable,
        bookmark=bookmark,
    )


@student_bp.route("/assignments/<int:assignment_id>/answers/<int:element_id>", methods=["POST"])
@login_required
@role_required("student")
def save_answer(assignment_id, element_id):
    assignment = _get_visible_assignment(assignment_id)
    submission = _get_or_create_submission(assignment)
    if submission.status not in (SUBMISSION_IN_PROGRESS, SUBMISSION_NEEDS_REVISION):
        abort(403, description="This assignment has already been submitted.")

    data = request.get_json(force=True) or {}
    answer = StudentAnswer.query.filter_by(
        submission_id=submission.id, worksheet_element_id=element_id
    ).first()
    if answer is None:
        answer = StudentAnswer(submission_id=submission.id, worksheet_element_id=element_id)
        db.session.add(answer)
    answer.answer_json = data.get("answer_json")
    db.session.commit()
    return jsonify({"status": "ok"})


@student_bp.route("/assignments/<int:assignment_id>/upload", methods=["POST"])
@login_required
@role_required("student")
def upload_answer_image(assignment_id):
    assignment = _get_visible_assignment(assignment_id)
    submission = _get_or_create_submission(assignment)
    if submission.status not in (SUBMISSION_IN_PROGRESS, SUBMISSION_NEEDS_REVISION):
        abort(403, description="This assignment has already been submitted.")

    element_id = request.form.get("element_id", type=int)
    upload = request.files.get("file")
    if not element_id or not upload or not upload.filename:
        abort(400, description="Missing file or element id.")

    file_path = save_upload(upload, assignment.subject.code)
    answer = StudentAnswer.query.filter_by(
        submission_id=submission.id, worksheet_element_id=element_id
    ).first()
    if answer is None:
        answer = StudentAnswer(submission_id=submission.id, worksheet_element_id=element_id)
        db.session.add(answer)
    answer.image_file_path = file_path
    db.session.commit()
    return jsonify({"status": "ok", "file_path": file_path})


@student_bp.route("/assignments/<int:assignment_id>/submit", methods=["POST"])
@login_required
@role_required("student")
def submit_assignment(assignment_id):
    assignment = _get_visible_assignment(assignment_id)
    submission = _get_or_create_submission(assignment)

    # A small grace window absorbs network/clock lag between the exam timer hitting
    # zero client-side and this request landing, so an on-time auto-submit isn't
    # rejected as "late" by a few seconds.
    grace = timedelta(minutes=2)
    if assignment.due_date and datetime.now(timezone.utc).replace(tzinfo=None) > assignment.due_date + grace:
        flash("The due date has passed — you can no longer submit this assignment.", "error")
        return redirect(url_for("student.assignment_detail", assignment_id=assignment.id))

    if submission.status in (SUBMISSION_IN_PROGRESS, SUBMISSION_NEEDS_REVISION):
        was_revision = submission.status == SUBMISSION_NEEDS_REVISION
        submission.status = SUBMISSION_SUBMITTED
        submission.submitted_at = datetime.now(timezone.utc)
        for answer in submission.answers:
            if answer.canvas_document is not None:
                canvas_service.lock_document(answer.canvas_document)
        db.session.commit()

        verb = "resubmitted" if was_revision else "submitted"
        create_notification(
            assignment.teacher_id,
            "submission_received",
            f"{current_user.full_name} {verb} {assignment.title}",
            link_url=url_for("teacher.grade_submission", submission_id=submission.id),
            related_object_type="submission",
            related_object_id=submission.id,
        )
        db.session.commit()
        flash("Assignment resubmitted." if was_revision else "Assignment submitted.", "success")
    return redirect(url_for("student.assignment_detail", assignment_id=assignment.id))
