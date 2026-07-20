from flask import jsonify, request, abort
from flask_login import login_required, current_user

from app.blueprints.api import api_bp
from app.constants import AI_MODE_HINTS_ONLY
from app.models.assignment import Assignment
from app.models.storybook import Storybook
from app.models.worksheet import WorksheetElement
from app.services import ai_hints
from app.services.exam_lockdown_guard import get_active_exam_session


@api_bp.route("/ai/hint", methods=["POST"])
@login_required
def get_ai_hint():
    data = request.get_json(force=True) or {}
    element = WorksheetElement.query.get_or_404(data.get("worksheet_element_id"))

    if not current_user.is_student:
        abort(403, description="Only students can request hints.")
    if get_active_exam_session(current_user) is not None:
        abort(403, description="AI assistance is disabled during an exam.")

    if data.get("assignment_id"):
        assignment = Assignment.query.get_or_404(data.get("assignment_id"))
        if assignment.ai_mode != AI_MODE_HINTS_ONLY:
            abort(403, description="AI assistance is not enabled for this assignment.")
        if element.worksheet_id != assignment.worksheet_id:
            abort(400, description="This question doesn't belong to this assignment.")
    elif data.get("storybook_id"):
        storybook = Storybook.query.get_or_404(data.get("storybook_id"))
        if storybook.ai_mode != AI_MODE_HINTS_ONLY:
            abort(403, description="AI assistance is not enabled for this storybook.")
        if element.worksheet_id != storybook.worksheet_id:
            abort(400, description="This question doesn't belong to this storybook.")
    else:
        abort(400, description="Provide assignment_id or storybook_id.")

    hint = ai_hints.get_hint(element)
    return jsonify({"hint": hint})
