from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.extensions import db
from app.models.academic import Enrollment
from app.models.assignment import Assignment
from app.models.group_collab import ProjectGroup, ProjectGroupMembership


def _get_owned_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id, teacher_id=current_user.id).first()
    if assignment is None:
        abort(404)
    return assignment


@teacher_bp.route("/assignments/<int:assignment_id>/groups", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def assignment_groups(assignment_id):
    assignment = _get_owned_assignment(assignment_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        student_ids = [int(sid) for sid in request.form.getlist("student_ids") if sid.isdigit()]
        enrolled_ids = {
            e.student_id
            for e in Enrollment.query.filter_by(class_group_id=assignment.class_group_id).all()
        }
        student_ids = [sid for sid in student_ids if sid in enrolled_ids]
        if not name:
            flash("Group name is required.", "error")
        else:
            assignment.is_group_assignment = True
            group = ProjectGroup(assignment_id=assignment.id, name=name)
            db.session.add(group)
            db.session.flush()
            for sid in student_ids:
                db.session.add(ProjectGroupMembership(group_id=group.id, student_id=sid))
            db.session.commit()
            flash("Group created.", "success")
        return redirect(url_for("teacher.assignment_groups", assignment_id=assignment.id))

    groups = ProjectGroup.query.filter_by(assignment_id=assignment.id).all()
    grouped_student_ids = {sid for g in groups for sid in g.student_ids}
    all_students = [
        e.student for e in Enrollment.query.filter_by(class_group_id=assignment.class_group_id).all()
    ]
    unassigned = [s for s in all_students if s.id not in grouped_student_ids]
    return render_template(
        "teacher/assignment_groups.html", assignment=assignment, groups=groups, unassigned=unassigned
    )


@teacher_bp.route("/assignments/<int:assignment_id>/groups/<int:group_id>/members", methods=["POST"])
@login_required
@role_required("teacher")
def group_add_member(assignment_id, group_id):
    assignment = _get_owned_assignment(assignment_id)
    group = ProjectGroup.query.filter_by(id=group_id, assignment_id=assignment.id).first_or_404()
    student_id = request.form.get("student_id", type=int)
    if student_id and not Enrollment.query.filter_by(
        class_group_id=assignment.class_group_id, student_id=student_id
    ).first():
        abort(400, description="Student is not enrolled in this class.")
    if student_id:
        existing = ProjectGroupMembership.query.filter_by(
            group_id=group.id, student_id=student_id
        ).first()
        if not existing:
            db.session.add(ProjectGroupMembership(group_id=group.id, student_id=student_id))
            db.session.commit()
    return redirect(url_for("teacher.assignment_groups", assignment_id=assignment.id))
