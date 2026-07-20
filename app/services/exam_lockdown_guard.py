from flask import request, redirect, url_for

from app.models.academic import Enrollment
from app.models.exam_lockdown import ExamSession, LockdownSession

EXEMPT_ENDPOINTS = {"static", "student.exam_active", "student.lockdown", "student.calculator"}

EXAM_ALLOWED_ENDPOINTS = {
    "student.assignment_detail",
    "student.save_answer",
    "student.upload_answer_image",
    "student.submit_assignment",
}

LOCKDOWN_ALLOWED_ENDPOINTS = {
    "student.assignment_detail",
    "student.save_answer",
    "student.upload_answer_image",
    "student.submit_assignment",
}


def get_active_exam_session(user):
    return ExamSession.query.filter_by(student_id=user.id, is_active=True).first()


def get_active_lockdown_session(user):
    class_ids = [e.class_group_id for e in Enrollment.query.filter_by(student_id=user.id).all()]
    if not class_ids:
        return None
    return LockdownSession.query.filter(
        LockdownSession.class_group_id.in_(class_ids), LockdownSession.is_active.is_(True)
    ).first()


def enforce_restrictions(user):
    """Call from student_bp.before_request. Returns a redirect Response to block the
    current request, or None to allow it through."""
    if request.endpoint in EXEMPT_ENDPOINTS:
        return None

    exam_session = get_active_exam_session(user)
    if exam_session is not None:
        if request.endpoint in EXAM_ALLOWED_ENDPOINTS:
            assignment_id = request.view_args.get("assignment_id") if request.view_args else None
            if assignment_id is not None and int(assignment_id) == exam_session.assignment_id:
                return None
        return redirect(url_for("student.exam_active"))

    lockdown_session = get_active_lockdown_session(user)
    if lockdown_session is not None:
        if request.endpoint in LOCKDOWN_ALLOWED_ENDPOINTS:
            assignment_id = request.view_args.get("assignment_id") if request.view_args else None
            if assignment_id is not None:
                from app.models.assignment import Assignment

                assignment = Assignment.query.get(assignment_id)
                if assignment and assignment.class_group_id == lockdown_session.class_group_id:
                    return None
        return redirect(url_for("student.lockdown"))

    return None


def document_allowed_during_exam(document, exam_session):
    """Used by the canvas API (a different blueprint) to scope canvas access to the
    active exam's own assignment when a student is mid-exam."""
    from app.models.assignment import StudentAnswer, Submission

    answer = StudentAnswer.query.filter_by(canvas_document_id=document.id).first()
    if answer is None:
        return False
    submission = Submission.query.get(answer.submission_id)
    return submission is not None and submission.assignment_id == exam_session.assignment_id
