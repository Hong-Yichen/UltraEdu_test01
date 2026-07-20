from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.constants import CANVAS_ELEMENT_TYPES, CANVAS_OWNER_MODEL_ANSWER
from app.extensions import db
from app.models.assignment import Assignment, ModelAnswer
from app.services import canvas_service


def _get_owned_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, teacher_id=current_user.id).first()
    if assignment is None:
        abort(404)
    return assignment


@teacher_bp.route("/assignments/<int:assignment_id>/model-answers", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def assignment_model_answers(assignment_id):
    assignment = _get_owned_assignment(assignment_id)
    if not assignment.worksheet:
        abort(404, description="This assignment has no worksheet to attach model answers to.")

    model_answers_by_element = {
        m.worksheet_element_id: m
        for m in ModelAnswer.query.filter_by(assignment_id=assignment.id).all()
        if m.worksheet_element_id is not None
    }

    if request.method == "POST":
        for element in assignment.worksheet.elements:
            text_notes = request.form.get(f"text_notes_{element.id}", "").strip()
            model_answer = model_answers_by_element.get(element.id)
            if model_answer is None:
                if text_notes:
                    db.session.add(
                        ModelAnswer(
                            assignment_id=assignment.id,
                            worksheet_element_id=element.id,
                            text_notes=text_notes,
                        )
                    )
            else:
                model_answer.text_notes = text_notes or None
        db.session.commit()
        flash("Model answers saved.", "success")
        return redirect(url_for("teacher.assignment_model_answers", assignment_id=assignment.id))

    # Lazily create a canvas for canvas-capable elements so the teacher can draw an
    # ideal answer, mirroring how a student's canvas answer is lazily created.
    for element in assignment.worksheet.elements:
        if element.element_type not in CANVAS_ELEMENT_TYPES:
            continue
        model_answer = model_answers_by_element.get(element.id)
        if model_answer is None:
            document = canvas_service.create_document(
                CANVAS_OWNER_MODEL_ANSWER, current_user.id, int(element.width), int(element.height)
            )
            model_answer = ModelAnswer(
                assignment_id=assignment.id,
                worksheet_element_id=element.id,
                canvas_document_id=document.id,
            )
            db.session.add(model_answer)
            model_answers_by_element[element.id] = model_answer
        elif model_answer.canvas_document_id is None:
            document = canvas_service.create_document(
                CANVAS_OWNER_MODEL_ANSWER, current_user.id, int(element.width), int(element.height)
            )
            model_answer.canvas_document_id = document.id
    db.session.commit()

    return render_template(
        "teacher/assignment_model_answers.html",
        assignment=assignment,
        model_answers_by_element=model_answers_by_element,
    )
