from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.constants import STORYBOOK_LANGUAGES, AI_MODES
from app.extensions import db
from app.models.academic import Subject
from app.models.worksheet import Worksheet
from app.models.storybook import Storybook, StorybookPage
from app.services.file_storage import save_upload


def _get_owned_storybook(storybook_id):
    storybook = Storybook.query.filter_by(id=storybook_id, created_by=current_user.id).first()
    if storybook is None:
        abort(404)
    return storybook


@teacher_bp.route("/storybooks")
@login_required
@role_required("teacher")
def storybooks_list():
    storybooks = (
        Storybook.query.filter_by(created_by=current_user.id)
        .order_by(Storybook.created_at.desc())
        .all()
    )
    return render_template("teacher/storybooks_list.html", storybooks=storybooks)


@teacher_bp.route("/storybooks/new", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def storybooks_new():
    subjects = Subject.query.order_by(Subject.name).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        language = request.form.get("language")
        subject_id = request.form.get("subject_id", type=int)
        description = request.form.get("description", "").strip()
        subject = Subject.query.get(subject_id) if subject_id else None

        errors = []
        if not title:
            errors.append("Title is required.")
        if language not in STORYBOOK_LANGUAGES:
            errors.append("Choose a language.")
        if subject is None:
            errors.append("Choose a subject.")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            storybook = Storybook(
                title=title,
                language=language,
                subject_id=subject.id,
                description=description or None,
                created_by=current_user.id,
            )
            db.session.add(storybook)
            db.session.commit()
            flash("Storybook created. Add pages below.", "success")
            return redirect(url_for("teacher.storybook_edit", storybook_id=storybook.id))

    return render_template(
        "teacher/storybooks_new.html", subjects=subjects, languages=STORYBOOK_LANGUAGES
    )


@teacher_bp.route("/storybooks/<int:storybook_id>", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def storybook_edit(storybook_id):
    storybook = _get_owned_storybook(storybook_id)
    worksheets = Worksheet.query.filter_by(
        teacher_id=current_user.id, subject_id=storybook.subject_id
    ).all()

    if request.method == "POST":
        text_content = request.form.get("text_content", "").strip()
        image = request.files.get("image")
        if not text_content:
            flash("Page text is required.", "error")
        else:
            image_path = None
            if image and image.filename:
                image_path = save_upload(image, storybook.subject.code)
            next_page_number = max([p.page_number for p in storybook.pages], default=0) + 1
            db.session.add(
                StorybookPage(
                    storybook_id=storybook.id,
                    page_number=next_page_number,
                    text_content=text_content,
                    image_path=image_path,
                )
            )
            db.session.commit()
            flash("Page added.", "success")
        return redirect(url_for("teacher.storybook_edit", storybook_id=storybook.id))

    return render_template(
        "teacher/storybook_edit.html", storybook=storybook, worksheets=worksheets, ai_modes=AI_MODES
    )


@teacher_bp.route("/storybooks/<int:storybook_id>/link-worksheet", methods=["POST"])
@login_required
@role_required("teacher")
def storybook_link_worksheet(storybook_id):
    storybook = _get_owned_storybook(storybook_id)
    worksheet_id = request.form.get("worksheet_id", type=int) or None
    if worksheet_id:
        worksheet = Worksheet.query.filter_by(id=worksheet_id, teacher_id=current_user.id).first()
        if worksheet is None:
            abort(400)
        storybook.worksheet_id = worksheet.id
    else:
        storybook.worksheet_id = None
    ai_mode = request.form.get("ai_mode")
    if ai_mode in AI_MODES:
        storybook.ai_mode = ai_mode
    db.session.commit()
    flash("Activities worksheet updated.", "success")
    return redirect(url_for("teacher.storybook_edit", storybook_id=storybook.id))
