import json

from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.constants import WORKSHEET_ELEMENT_TYPES
from app.extensions import db
from app.models.academic import Subject
from app.models.worksheet import Worksheet, WorksheetElement

DEFAULT_SIZES = {
    "multiple_choice": (360, 140),
    "fill_blank": (400, 190),
    "matching": (360, 180),
    "label_diagram": (400, 300),
    "drawing_area": (450, 320),
    "handwriting_area": (600, 320),
    "image_upload": (300, 100),
    "text_highlight": (500, 200),
}


def _get_owned_worksheet(worksheet_id):
    worksheet = Worksheet.query.filter_by(id=worksheet_id, teacher_id=current_user.id).first()
    if worksheet is None:
        abort(404)
    return worksheet


@teacher_bp.route("/worksheets")
@login_required
@role_required("teacher")
def worksheets_list():
    worksheets = (
        Worksheet.query.filter_by(teacher_id=current_user.id)
        .order_by(Worksheet.created_at.desc())
        .all()
    )
    return render_template("teacher/worksheets_list.html", worksheets=worksheets)


@teacher_bp.route("/worksheets/<int:worksheet_id>/delete", methods=["POST"])
@login_required
@role_required("teacher")
def worksheets_delete(worksheet_id):
    worksheet = _get_owned_worksheet(worksheet_id)

    from app.models.assignment import Assignment
    from app.models.storybook import Storybook

    in_use_assignments = Assignment.query.filter_by(worksheet_id=worksheet.id).count()
    in_use_storybooks = Storybook.query.filter_by(worksheet_id=worksheet.id).count()
    if in_use_assignments or in_use_storybooks:
        flash(
            "This worksheet is still linked to an assignment or storybook — "
            "unlink or remove those first before deleting it.",
            "error",
        )
        return redirect(url_for("teacher.worksheets_list"))

    db.session.delete(worksheet)
    db.session.commit()
    flash("Worksheet removed.", "success")
    return redirect(url_for("teacher.worksheets_list"))


@teacher_bp.route("/worksheets/new", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def worksheets_new():
    subjects = Subject.academic_query().order_by(Subject.name).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject_id = request.form.get("subject_id", type=int)
        subject = Subject.query.get(subject_id) if subject_id else None
        if subject is not None and not subject.is_academic:
            subject = None
        if not title or subject is None:
            flash("Title and subject are required.", "error")
        else:
            worksheet = Worksheet(title=title, subject_id=subject.id, teacher_id=current_user.id)
            db.session.add(worksheet)
            db.session.commit()
            return redirect(url_for("teacher.worksheet_builder", worksheet_id=worksheet.id))
    return render_template("teacher/worksheets_new.html", subjects=subjects)


@teacher_bp.route("/worksheets/<int:worksheet_id>/builder")
@login_required
@role_required("teacher")
def worksheet_builder(worksheet_id):
    worksheet = _get_owned_worksheet(worksheet_id)
    elements_json = json.dumps(
        [_serialize_element(e) for e in worksheet.elements]
    ).replace("</", "<\\/")
    return render_template(
        "teacher/worksheet_builder.html",
        worksheet=worksheet,
        element_types=WORKSHEET_ELEMENT_TYPES,
        elements_json=elements_json,
    )


def _serialize_element(el):
    return {
        "id": el.id,
        "element_type": el.element_type,
        "page_number": el.page_number,
        "order_index": el.order_index,
        "x": el.x,
        "y": el.y,
        "width": el.width,
        "height": el.height,
        "prompt_text": el.prompt_text,
        "points": el.points,
        "config_json": el.config_json,
    }


@teacher_bp.route("/worksheets/<int:worksheet_id>/elements", methods=["POST"])
@login_required
@role_required("teacher")
def worksheet_elements_create(worksheet_id):
    worksheet = _get_owned_worksheet(worksheet_id)
    data = request.get_json(force=True) or {}
    element_type = data.get("element_type")
    if element_type not in WORKSHEET_ELEMENT_TYPES:
        abort(400, description="Invalid element type.")
    default_w, default_h = DEFAULT_SIZES.get(element_type, (300, 100))
    max_order = max([e.order_index for e in worksheet.elements], default=-1)
    element = WorksheetElement(
        worksheet_id=worksheet.id,
        element_type=element_type,
        page_number=data.get("page_number", 1),
        order_index=max_order + 1,
        x=data.get("x", 40),
        y=data.get("y", 40),
        width=data.get("width", default_w),
        height=data.get("height", default_h),
        prompt_text=data.get("prompt_text", ""),
        points=data.get("points", 1),
        config_json=data.get("config_json", {}),
    )
    db.session.add(element)
    db.session.commit()
    return jsonify(_serialize_element(element)), 201


@teacher_bp.route("/worksheets/<int:worksheet_id>/elements/<int:element_id>", methods=["PATCH"])
@login_required
@role_required("teacher")
def worksheet_elements_update(worksheet_id, element_id):
    worksheet = _get_owned_worksheet(worksheet_id)
    element = WorksheetElement.query.filter_by(id=element_id, worksheet_id=worksheet.id).first()
    if element is None:
        abort(404)
    data = request.get_json(force=True) or {}
    for field in ("x", "y", "width", "height", "prompt_text", "points", "config_json", "page_number"):
        if field in data:
            setattr(element, field, data[field])
    db.session.commit()
    return jsonify(_serialize_element(element))


@teacher_bp.route("/worksheets/<int:worksheet_id>/elements/<int:element_id>", methods=["DELETE"])
@login_required
@role_required("teacher")
def worksheet_elements_delete(worksheet_id, element_id):
    worksheet = _get_owned_worksheet(worksheet_id)
    element = WorksheetElement.query.filter_by(id=element_id, worksheet_id=worksheet.id).first()
    if element is None:
        abort(404)
    db.session.delete(element)
    db.session.commit()
    return jsonify({"status": "ok"})
