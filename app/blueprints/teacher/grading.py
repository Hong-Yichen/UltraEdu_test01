from datetime import datetime, timezone

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.constants import SUBMISSION_GRADED, SUBMISSION_NEEDS_REVISION, SUBMISSION_IN_PROGRESS
from app.extensions import db
from app.models.assignment import Submission, VoiceFeedback
from app.services import canvas_service
from app.services.file_storage import save_upload


def _get_gradable_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.assignment is None or submission.assignment.teacher_id != current_user.id:
        abort(404)
    return submission


@teacher_bp.route("/submissions/<int:submission_id>/grade", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def grade_submission(submission_id):
    submission = _get_gradable_submission(submission_id)
    assignment = submission.assignment

    if request.method == "POST":
        action = request.form.get("action", "return")
        score = request.form.get("score", type=int)
        feedback_text = request.form.get("feedback_text", "").strip()
        submission.score = score
        submission.feedback_text = feedback_text or None
        submission.graded_by = current_user.id
        submission.graded_at = datetime.now(timezone.utc)

        voice_file = request.files.get("voice_feedback")
        if voice_file and voice_file.filename:
            file_path = save_upload(voice_file, assignment.subject.code)
            if submission.voice_feedback is None:
                db.session.add(
                    VoiceFeedback(
                        submission_id=submission.id,
                        audio_file_path=file_path,
                        recorded_by=current_user.id,
                        recorded_at=datetime.now(timezone.utc),
                    )
                )
            else:
                submission.voice_feedback.audio_file_path = file_path
                submission.voice_feedback.recorded_by = current_user.id
                submission.voice_feedback.recorded_at = datetime.now(timezone.utc)

        from app.services.notifications_service import create_notification

        if action == "return_for_corrections":
            submission.status = SUBMISSION_NEEDS_REVISION
            for answer in submission.answers:
                if answer.canvas_document is not None:
                    canvas_service.unlock_document(answer.canvas_document)
            db.session.commit()
            if submission.student_id:
                create_notification(
                    submission.student_id,
                    "revision_requested",
                    f"Corrections needed on {assignment.title}",
                    feedback_text or "Your teacher asked you to make some corrections.",
                    link_url=url_for("student.assignment_detail", assignment_id=assignment.id),
                    related_object_type="submission",
                    related_object_id=submission.id,
                )
                db.session.commit()
            flash("Returned to the student for corrections.", "success")
        else:
            submission.status = SUBMISSION_GRADED
            db.session.commit()
            if submission.student_id:
                create_notification(
                    submission.student_id,
                    "feedback_received",
                    f"Feedback on {assignment.title}",
                    feedback_text or None,
                    link_url=url_for("student.assignment_detail", assignment_id=assignment.id),
                    related_object_type="submission",
                    related_object_id=submission.id,
                )
                db.session.commit()
            flash("Returned to the student with feedback.", "success")

        return redirect(url_for("teacher.assignment_detail", assignment_id=assignment.id))

    answers_by_element = {a.worksheet_element_id: a for a in submission.answers}
    model_answers_by_element = {}
    if assignment.worksheet:
        from app.models.assignment import ModelAnswer

        model_answers_by_element = {
            m.worksheet_element_id: m
            for m in ModelAnswer.query.filter_by(assignment_id=assignment.id).all()
            if m.worksheet_element_id is not None
        }

    return render_template(
        "teacher/grade_submission.html",
        submission=submission,
        assignment=assignment,
        answers_by_element=answers_by_element,
        model_answers_by_element=model_answers_by_element,
    )
