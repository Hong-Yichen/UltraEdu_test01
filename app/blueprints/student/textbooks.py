from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.constants import CANVAS_OWNER_TEXTBOOK_PAGE
from app.extensions import db
from app.models.academic import Enrollment, ClassGroup
from app.models.textbook import Textbook, TextbookNote, TextbookPageAnnotation
from app.services import canvas_service


def _visible_textbooks_query(student_id):
    class_ids = [e.class_group_id for e in Enrollment.query.filter_by(student_id=student_id).all()]
    if not class_ids:
        return Textbook.query.filter(Textbook.id.is_(None))
    subject_ids = [c.subject_id for c in ClassGroup.query.filter(ClassGroup.id.in_(class_ids)).all()]
    # A textbook aimed at one of my classes is visible regardless of its subject tag
    # (the class assignment is the more specific, authoritative scope). A school-wide
    # textbook (no class set) still needs to match a subject I actually take.
    return Textbook.query.filter(
        Textbook.published_at.isnot(None),
        db.or_(
            Textbook.class_group_id.in_(class_ids),
            db.and_(Textbook.class_group_id.is_(None), Textbook.subject_id.in_(subject_ids)),
        ),
    )


def _get_visible_textbook(textbook_id, student_id):
    textbook = _visible_textbooks_query(student_id).filter(Textbook.id == textbook_id).first()
    if textbook is None:
        abort(404)
    return textbook


@student_bp.route("/textbooks")
@login_required
@role_required("student")
def textbooks_list():
    textbooks = _visible_textbooks_query(current_user.id).order_by(Textbook.created_at.desc()).all()
    return render_template("student/textbooks_list.html", textbooks=textbooks)


@student_bp.route("/textbooks/<int:textbook_id>")
@login_required
@role_required("student")
def textbook_reader(textbook_id):
    textbook = _get_visible_textbook(textbook_id, current_user.id)
    notes = (
        TextbookNote.query.filter_by(textbook_id=textbook.id, student_id=current_user.id)
        .order_by(TextbookNote.page_number.is_(None), TextbookNote.page_number, TextbookNote.created_at)
        .all()
    )
    return render_template("student/textbook_reader.html", textbook=textbook, notes=notes)


@student_bp.route("/textbooks/<int:textbook_id>/pages/<int:page_number>/canvas", methods=["POST"])
@login_required
@role_required("student")
def textbook_page_canvas(textbook_id, page_number):
    textbook = _get_visible_textbook(textbook_id, current_user.id)
    annotation = TextbookPageAnnotation.query.filter_by(
        textbook_id=textbook.id, student_id=current_user.id, page_number=page_number
    ).first()
    if annotation is None:
        data = request.get_json(silent=True) or {}
        width = data.get("width") or 800
        height = data.get("height") or 1050
        document = canvas_service.create_document(
            CANVAS_OWNER_TEXTBOOK_PAGE, current_user.id, int(width), int(height)
        )
        annotation = TextbookPageAnnotation(
            textbook_id=textbook.id,
            student_id=current_user.id,
            page_number=page_number,
            canvas_document_id=document.id,
        )
        db.session.add(annotation)
        db.session.commit()
    return jsonify(
        {
            "document_id": annotation.canvas_document_id,
            "width": annotation.canvas_document.width,
            "height": annotation.canvas_document.height,
        }
    )


@student_bp.route("/textbooks/<int:textbook_id>/notes", methods=["POST"])
@login_required
@role_required("student")
def textbook_note_create(textbook_id):
    textbook = _get_visible_textbook(textbook_id, current_user.id)
    body = request.form.get("body", "").strip()
    page_number = request.form.get("page_number", type=int)
    if not body:
        flash("Note can't be empty.", "error")
    else:
        db.session.add(
            TextbookNote(
                textbook_id=textbook.id, student_id=current_user.id,
                page_number=page_number, body=body,
            )
        )
        db.session.commit()
    return redirect(url_for("student.textbook_reader", textbook_id=textbook.id))


@student_bp.route("/textbooks/<int:textbook_id>/notes/<int:note_id>/delete", methods=["POST"])
@login_required
@role_required("student")
def textbook_note_delete(textbook_id, note_id):
    note = TextbookNote.query.filter_by(
        id=note_id, textbook_id=textbook_id, student_id=current_user.id
    ).first()
    if note is None:
        abort(404)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("student.textbook_reader", textbook_id=textbook_id))
