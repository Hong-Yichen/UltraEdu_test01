from flask import jsonify, request, abort
from flask_login import login_required, current_user

from app.blueprints.api import api_bp
from app.extensions import db
from app.models.canvas import CanvasDocument, CanvasStroke
from app.services import canvas_service
from app.services.canvas_service import CanvasPermissionError
from app.services.exam_lockdown_guard import get_active_exam_session, document_allowed_during_exam


def _check_exam_scope(document):
    """During an active exam, a student may only touch canvas documents belonging to
    that exam's own assignment — blocks reaching unrelated documents by id."""
    if not current_user.is_student:
        return
    exam_session = get_active_exam_session(current_user)
    if exam_session is not None and not document_allowed_during_exam(document, exam_session):
        abort(403, description="This canvas isn't part of your current exam.")


@api_bp.route("/canvas/documents", methods=["POST"])
@login_required
def create_canvas_document():
    data = request.get_json(force=True) or {}
    owner_type = data.get("owner_type", "student_answer")
    width = data.get("width", 800)
    height = data.get("height", 400)
    background_image_path = data.get("background_image_path")
    document = canvas_service.create_document(
        owner_type, current_user.id, width, height, background_image_path
    )
    return jsonify(canvas_service.get_document_state(document)), 201


@api_bp.route("/canvas/documents/<int:document_id>", methods=["GET"])
@login_required
def get_canvas_document(document_id):
    document = CanvasDocument.query.get_or_404(document_id)
    _check_exam_scope(document)
    return jsonify(canvas_service.get_document_state(document))


@api_bp.route("/canvas/documents/<int:document_id>/sync", methods=["POST"])
@login_required
def sync_canvas_document(document_id):
    document = CanvasDocument.query.get_or_404(document_id)
    _check_exam_scope(document)
    data = request.get_json(force=True) or {}
    try:
        created_strokes, created_notes = canvas_service.sync_document(
            document,
            current_user,
            data.get("new_strokes", []),
            data.get("deleted_stroke_ids", []),
            data.get("sticky_notes", []),
        )
    except CanvasPermissionError as e:
        abort(403, description=str(e))
    return jsonify(
        {
            "created_stroke_ids": [s.id for s in created_strokes],
            "created_sticky_note_ids": [n.id for n in created_notes],
        }
    )


@api_bp.route("/canvas/strokes/<int:stroke_id>", methods=["PATCH"])
@login_required
def patch_stroke(stroke_id):
    stroke = CanvasStroke.query.get_or_404(stroke_id)
    document = CanvasDocument.query.get_or_404(stroke.canvas_document_id)
    _check_exam_scope(document)
    data = request.get_json(force=True) or {}
    if data.get("is_deleted") is True:
        if not canvas_service.can_write_layer(document, current_user, stroke.layer):
            abort(403, description="Not permitted to erase this stroke.")
        stroke.is_deleted = True
        db.session.commit()
    return jsonify({"status": "ok"})
