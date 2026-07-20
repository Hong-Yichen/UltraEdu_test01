from flask import render_template, request, jsonify, abort
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.extensions import db
from app.models.bookmark import Bookmark


@student_bp.route("/bookmarks")
@login_required
@role_required("student")
def bookmarks_list():
    bookmarks = (
        Bookmark.query.filter_by(student_id=current_user.id)
        .order_by(Bookmark.subject_id, Bookmark.created_at.desc())
        .all()
    )
    return render_template("student/bookmarks_list.html", bookmarks=bookmarks)


@student_bp.route("/bookmarks", methods=["POST"])
@login_required
@role_required("student")
def bookmarks_create():
    data = request.get_json(force=True) or {}
    subject_id = data.get("subject_id")
    assignment_id = data.get("assignment_id")
    resource_id = data.get("resource_id")
    storybook_id = data.get("storybook_id")
    if not subject_id or sum(bool(x) for x in (assignment_id, resource_id, storybook_id)) != 1:
        abort(400, description="Provide subject_id and exactly one of assignment_id/resource_id/storybook_id.")

    existing = Bookmark.query.filter_by(
        student_id=current_user.id,
        assignment_id=assignment_id,
        resource_id=resource_id,
        storybook_id=storybook_id,
    ).first()
    if existing:
        return jsonify({"bookmarked": True, "id": existing.id})

    bookmark = Bookmark(
        student_id=current_user.id,
        subject_id=subject_id,
        assignment_id=assignment_id,
        resource_id=resource_id,
        storybook_id=storybook_id,
    )
    db.session.add(bookmark)
    db.session.commit()
    return jsonify({"bookmarked": True, "id": bookmark.id}), 201


@student_bp.route("/bookmarks/<int:bookmark_id>", methods=["DELETE"])
@login_required
@role_required("student")
def bookmarks_delete(bookmark_id):
    bookmark = Bookmark.query.filter_by(id=bookmark_id, student_id=current_user.id).first()
    if bookmark is None:
        abort(404)
    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({"bookmarked": False})
