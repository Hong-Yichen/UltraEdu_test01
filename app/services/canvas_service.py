from app.extensions import db
from app.models.canvas import CanvasDocument, CanvasStroke, StickyNote


class CanvasPermissionError(Exception):
    pass


def create_document(owner_type, created_by, width, height, background_image_path=None):
    document = CanvasDocument(
        owner_type=owner_type,
        created_by=created_by,
        width=width,
        height=height,
        background_image_path=background_image_path,
    )
    db.session.add(document)
    db.session.commit()
    return document


def get_document_state(document):
    strokes = [s for s in document.strokes if not s.is_deleted]
    return {
        "id": document.id,
        "owner_type": document.owner_type,
        "width": document.width,
        "height": document.height,
        "background_image_path": document.background_image_path,
        "is_locked": document.is_locked,
        "strokes": [_serialize_stroke(s) for s in strokes],
        "sticky_notes": [_serialize_sticky_note(n) for n in document.sticky_notes],
    }


def _serialize_stroke(stroke):
    return {
        "id": stroke.id,
        "layer": stroke.layer,
        "tool": stroke.tool,
        "color": stroke.color,
        "width": stroke.width,
        "opacity": stroke.opacity,
        "points": stroke.points_json.get("points", []),
        "sequence": stroke.sequence,
        "author_id": stroke.author_id,
    }


def _serialize_sticky_note(note):
    return {
        "id": note.id,
        "x": note.x,
        "y": note.y,
        "width": note.width,
        "height": note.height,
        "text": note.text,
        "color": note.color,
        "author_id": note.author_id,
    }


def can_write_layer(document, user, layer):
    """Base-layer write rules: only the document's creator, and only while unlocked.
    Annotation-layer write rules: only once the document is locked, and only a teacher.

    NOTE: this is the baseline rule used while the canvas engine is validated in isolation.
    Once wired into Submission/StudentAnswer (assignments task), ownership resolution is
    tightened to check the actual assignment's enrolled student / grading teacher rather
    than "any teacher" — see services/canvas_service.py usage in blueprints/teacher/grading.py.
    """
    if layer == "base":
        return (not document.is_locked) and user.id == document.created_by
    if layer == "annotation":
        return document.is_locked and user.is_teacher
    return False


def sync_document(document, user, new_strokes, deleted_stroke_ids, sticky_notes):
    """Apply a batch sync payload. Raises CanvasPermissionError if the user may not write
    the layer(s) referenced by the payload."""
    max_sequence = max([s.sequence for s in document.strokes], default=-1)

    created_strokes = []
    for raw in new_strokes:
        layer = raw.get("layer", "base")
        if not can_write_layer(document, user, layer):
            raise CanvasPermissionError(f"Not permitted to write layer '{layer}' on this document.")
        max_sequence += 1
        stroke = CanvasStroke(
            canvas_document_id=document.id,
            author_id=user.id,
            layer=layer,
            tool=raw.get("tool", "pen"),
            color=raw.get("color", "#1a1a1a"),
            width=raw.get("width", 2.0),
            opacity=raw.get("opacity", 1.0),
            points_json={"points": raw.get("points", [])},
            sequence=max_sequence,
        )
        db.session.add(stroke)
        created_strokes.append(stroke)

    if deleted_stroke_ids:
        strokes = CanvasStroke.query.filter(
            CanvasStroke.id.in_(deleted_stroke_ids), CanvasStroke.canvas_document_id == document.id
        ).all()
        for stroke in strokes:
            if not can_write_layer(document, user, stroke.layer):
                raise CanvasPermissionError(f"Not permitted to erase layer '{stroke.layer}'.")
            stroke.is_deleted = True

    created_notes = []
    for raw in sticky_notes or []:
        if not can_write_layer(document, user, raw.get("layer", "base")):
            raise CanvasPermissionError("Not permitted to add sticky notes on this document.")
        note = StickyNote(
            canvas_document_id=document.id,
            author_id=user.id,
            x=raw.get("x", 0),
            y=raw.get("y", 0),
            width=raw.get("width", 160),
            height=raw.get("height", 120),
            text=raw.get("text", ""),
            color=raw.get("color", "#fff3b0"),
        )
        db.session.add(note)
        created_notes.append(note)

    db.session.commit()
    return created_strokes, created_notes


def lock_document(document):
    document.is_locked = True
    db.session.commit()


def unlock_document(document):
    document.is_locked = False
    db.session.commit()
