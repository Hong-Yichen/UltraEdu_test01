from datetime import datetime, timezone

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.extensions import db
from app.models.academic import ClassGroup
from app.models.exam_lockdown import LockdownSession
from app.models.resource import Resource


def _get_owned_class(class_group_id):
    class_group = ClassGroup.query.filter_by(id=class_group_id, teacher_id=current_user.id).first()
    if class_group is None:
        abort(404)
    return class_group


@teacher_bp.route("/classes/<int:class_group_id>/lockdown", methods=["GET"])
@login_required
@role_required("teacher")
def lockdown_control(class_group_id):
    class_group = _get_owned_class(class_group_id)
    active = LockdownSession.query.filter_by(class_group_id=class_group.id, is_active=True).first()
    resources = Resource.query.filter_by(subject_id=class_group.subject_id).all()
    return render_template(
        "teacher/lockdown_control.html", class_group=class_group, active=active, resources=resources
    )


@teacher_bp.route("/classes/<int:class_group_id>/lockdown/activate", methods=["POST"])
@login_required
@role_required("teacher")
def lockdown_activate(class_group_id):
    class_group = _get_owned_class(class_group_id)
    LockdownSession.query.filter_by(class_group_id=class_group.id, is_active=True).update(
        {"is_active": False, "ended_at": datetime.now(timezone.utc)}
    )
    resource_ids = [int(i) for i in request.form.getlist("resource_ids")]
    db.session.add(
        LockdownSession(
            class_group_id=class_group.id,
            teacher_id=current_user.id,
            subject_id=class_group.subject_id,
            allowed_resource_ids=resource_ids,
        )
    )
    db.session.commit()
    flash("Classroom Lockdown activated.", "success")
    return redirect(url_for("teacher.lockdown_control", class_group_id=class_group.id))


@teacher_bp.route("/classes/<int:class_group_id>/lockdown/deactivate", methods=["POST"])
@login_required
@role_required("teacher")
def lockdown_deactivate(class_group_id):
    class_group = _get_owned_class(class_group_id)
    LockdownSession.query.filter_by(class_group_id=class_group.id, is_active=True).update(
        {"is_active": False, "ended_at": datetime.now(timezone.utc)}
    )
    db.session.commit()
    flash("Classroom Lockdown ended.", "success")
    return redirect(url_for("teacher.lockdown_control", class_group_id=class_group.id))
