from flask import render_template, request, jsonify, abort
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.constants import CANVAS_ELEMENT_TYPES, SUBMISSION_IN_PROGRESS
from app.extensions import db
from app.models.storybook import Storybook
from app.models.assignment import Submission, StudentAnswer
from app.services import canvas_service


@student_bp.route("/storybooks")
@login_required
@role_required("student")
def storybooks_list():
    storybooks = Storybook.query.order_by(Storybook.language, Storybook.title).all()
    return render_template("student/storybooks_list.html", storybooks=storybooks)


def _get_or_create_storybook_submission(storybook):
    submission = Submission.query.filter_by(
        storybook_id=storybook.id, student_id=current_user.id
    ).first()
    if submission is None:
        submission = Submission(
            storybook_id=storybook.id, student_id=current_user.id, status=SUBMISSION_IN_PROGRESS
        )
        db.session.add(submission)
        db.session.commit()
    return submission


@student_bp.route("/storybooks/<int:storybook_id>")
@login_required
@role_required("student")
def storybook_detail(storybook_id):
    storybook = Storybook.query.get_or_404(storybook_id)
    answers_by_element = {}
    submission = None
    if storybook.worksheet_id:
        submission = _get_or_create_storybook_submission(storybook)
        answers_by_element = {a.worksheet_element_id: a for a in submission.answers}
        for element in storybook.worksheet.elements:
            if element.element_type in CANVAS_ELEMENT_TYPES and element.id not in answers_by_element:
                document = canvas_service.create_document(
                    "storybook_activity", current_user.id, int(element.width), int(element.height)
                )
                answer = StudentAnswer(
                    submission_id=submission.id, worksheet_element_id=element.id,
                    canvas_document_id=document.id,
                )
                db.session.add(answer)
                answers_by_element[element.id] = answer
        db.session.commit()
    return render_template(
        "student/storybook_detail.html",
        storybook=storybook,
        submission=submission,
        answers_by_element=answers_by_element,
    )


@student_bp.route("/storybooks/<int:storybook_id>/answers/<int:element_id>", methods=["POST"])
@login_required
@role_required("student")
def storybook_save_answer(storybook_id, element_id):
    storybook = Storybook.query.get_or_404(storybook_id)
    submission = _get_or_create_storybook_submission(storybook)
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
