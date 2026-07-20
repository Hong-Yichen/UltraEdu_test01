from datetime import date, datetime

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.blueprints.teacher import teacher_bp
from app.decorators import role_required
from app.constants import CALENDAR_EVENT_TYPES
from app.extensions import db
from app.models.academic import ClassGroup
from app.models.calendar_event import CalendarEvent
from app.services import calendar_service


def _get_owned_event(event_id):
    event = CalendarEvent.query.filter_by(id=event_id, created_by=current_user.id).first()
    if event is None:
        abort(404)
    return event


@teacher_bp.route("/calendar")
@login_required
@role_required("teacher")
def calendar_view():
    year = request.args.get("year", type=int) or date.today().year
    month = request.args.get("month", type=int) or date.today().month

    weeks = calendar_service.get_month_weeks(year, month)
    grid_start, grid_end = weeks[0][0], weeks[-1][-1]

    classes = ClassGroup.query.filter_by(teacher_id=current_user.id).all()
    class_ids = [c.id for c in classes]

    events = calendar_service.get_calendar_events(class_ids, grid_start, grid_end)
    assignments = calendar_service.get_assignment_due_dates(class_ids, grid_start, grid_end, published_only=False)

    day_map = calendar_service.build_day_map(
        events, assignments,
        event_url=lambda e: url_for("teacher.calendar_event_edit", event_id=e.id) if e.created_by == current_user.id else None,
        assignment_url=lambda a: url_for("teacher.assignment_detail", assignment_id=a.id),
    )

    py, pm = calendar_service.prev_month(year, month)
    ny, nm = calendar_service.next_month(year, month)

    return render_template(
        "teacher/calendar.html",
        year=year, month=month, month_name=calendar_service.MONTH_NAMES[month - 1],
        weeks=weeks, day_map=day_map, today=date.today(),
        prev_url=url_for("teacher.calendar_view", year=py, month=pm),
        next_url=url_for("teacher.calendar_view", year=ny, month=nm),
    )


@teacher_bp.route("/calendar/new", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def calendar_event_new():
    classes = ClassGroup.query.filter_by(teacher_id=current_user.id).all()
    default_date = request.args.get("date", date.today().isoformat())

    if request.method == "POST":
        event = _build_event_from_form(CalendarEvent(created_by=current_user.id), classes)
        if event:
            db.session.add(event)
            db.session.commit()
            flash("Event added to the calendar.", "success")
            return redirect(url_for("teacher.calendar_view", year=event.start_date.year, month=event.start_date.month))

    return render_template(
        "teacher/calendar_event_form.html", classes=classes, event_types=CALENDAR_EVENT_TYPES,
        default_date=default_date, event=None,
    )


@teacher_bp.route("/calendar/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def calendar_event_edit(event_id):
    event = _get_owned_event(event_id)
    classes = ClassGroup.query.filter_by(teacher_id=current_user.id).all()

    if request.method == "POST":
        updated = _build_event_from_form(event, classes)
        if updated:
            db.session.commit()
            flash("Event updated.", "success")
            return redirect(url_for("teacher.calendar_view", year=event.start_date.year, month=event.start_date.month))

    return render_template(
        "teacher/calendar_event_form.html", classes=classes, event_types=CALENDAR_EVENT_TYPES,
        default_date=event.start_date.isoformat(), event=event,
    )


@teacher_bp.route("/calendar/<int:event_id>/delete", methods=["POST"])
@login_required
@role_required("teacher")
def calendar_event_delete(event_id):
    event = _get_owned_event(event_id)
    year, month = event.start_date.year, event.start_date.month
    db.session.delete(event)
    db.session.commit()
    flash("Event removed.", "success")
    return redirect(url_for("teacher.calendar_view", year=year, month=month))


def _build_event_from_form(event, classes):
    title = request.form.get("title", "").strip()
    event_type = request.form.get("event_type", "school_event")
    start_raw = request.form.get("start_date", "")
    end_raw = request.form.get("end_date", "") or start_raw
    class_group_id = request.form.get("class_group_id", type=int) or None
    description = request.form.get("description", "").strip()

    errors = []
    if not title:
        errors.append("Title is required.")
    if event_type not in CALENDAR_EVENT_TYPES:
        errors.append("Invalid event type.")
    try:
        start_date = datetime.strptime(start_raw, "%Y-%m-%d").date()
    except ValueError:
        errors.append("Invalid start date.")
        start_date = None
    try:
        end_date = datetime.strptime(end_raw, "%Y-%m-%d").date()
    except ValueError:
        errors.append("Invalid end date.")
        end_date = None
    if start_date and end_date and end_date < start_date:
        errors.append("End date must be on or after the start date.")
    if class_group_id and class_group_id not in [c.id for c in classes]:
        errors.append("Invalid class.")

    if errors:
        for e in errors:
            flash(e, "error")
        return None

    event.title = title
    event.description = description or None
    event.event_type = event_type
    event.start_date = start_date
    event.end_date = end_date
    event.class_group_id = class_group_id
    return event
