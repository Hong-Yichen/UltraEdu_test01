from datetime import date

from flask import render_template, request, url_for
from flask_login import login_required, current_user

from app.blueprints.student import student_bp
from app.decorators import role_required
from app.models.academic import Enrollment
from app.services import calendar_service


@student_bp.route("/calendar")
@login_required
@role_required("student")
def calendar_view():
    year = request.args.get("year", type=int) or date.today().year
    month = request.args.get("month", type=int) or date.today().month

    weeks = calendar_service.get_month_weeks(year, month)
    grid_start, grid_end = weeks[0][0], weeks[-1][-1]

    class_ids = [e.class_group_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()]

    events = calendar_service.get_calendar_events(class_ids, grid_start, grid_end)
    assignments = calendar_service.get_assignment_due_dates(class_ids, grid_start, grid_end, published_only=True)

    day_map = calendar_service.build_day_map(
        events, assignments,
        assignment_url=lambda a: url_for("student.assignment_detail", assignment_id=a.id),
    )

    py, pm = calendar_service.prev_month(year, month)
    ny, nm = calendar_service.next_month(year, month)

    return render_template(
        "student/calendar.html",
        year=year, month=month, month_name=calendar_service.MONTH_NAMES[month - 1],
        weeks=weeks, day_map=day_map, today=date.today(),
        prev_url=url_for("student.calendar_view", year=py, month=pm),
        next_url=url_for("student.calendar_view", year=ny, month=nm),
    )
