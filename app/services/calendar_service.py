import calendar
from datetime import date, timedelta

from app.constants import CALENDAR_EVENT_COLORS
from app.models.calendar_event import CalendarEvent
from app.models.assignment import Assignment

MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def month_bounds(year, month):
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, 1), date(year, month, last_day)


def prev_month(year, month):
    return (year - 1, 12) if month == 1 else (year, month - 1)


def next_month(year, month):
    return (year + 1, 1) if month == 12 else (year, month + 1)


def get_month_weeks(year, month):
    """Returns a list of weeks (Mon-Sun), each a list of date objects, padded with
    leading/trailing days from adjacent months so every week has 7 entries."""
    cal = calendar.Calendar(firstweekday=0)
    return list(cal.monthdatescalendar(year, month))


def get_calendar_events(class_ids, grid_start, grid_end):
    """Events visible to the given classes (or school-wide) overlapping the grid range."""
    query = CalendarEvent.query.filter(
        CalendarEvent.start_date <= grid_end, CalendarEvent.end_date >= grid_start
    )
    if class_ids:
        query = query.filter(
            (CalendarEvent.class_group_id.is_(None)) | (CalendarEvent.class_group_id.in_(class_ids))
        )
    else:
        query = query.filter(CalendarEvent.class_group_id.is_(None))
    return query.all()


def get_assignment_due_dates(class_ids, grid_start, grid_end, published_only=True):
    if not class_ids:
        return []
    query = Assignment.query.filter(
        Assignment.class_group_id.in_(class_ids),
        Assignment.due_date.isnot(None),
        Assignment.due_date >= grid_start,
        Assignment.due_date <= grid_end + timedelta(days=1),
    )
    if published_only:
        query = query.filter(Assignment.published_at.isnot(None))
    return query.all()


def build_day_map(events, assignments, event_url=None, assignment_url=None):
    """Map date -> list of {label, color, url} entries for rendering in the grid.

    event_url / assignment_url are optional callables (obj -> url) so callers can
    link chips through to an edit or detail page without this module depending on
    Flask's request/url_for context.
    """
    day_map = {}

    def add(d, label, color, url=None):
        day_map.setdefault(d, []).append({"label": label, "color": color, "url": url})

    for event in events:
        cur = event.start_date
        while cur <= event.end_date:
            add(
                cur, event.title, CALENDAR_EVENT_COLORS.get(event.event_type, "sky"),
                event_url(event) if event_url else None,
            )
            cur += timedelta(days=1)

    for a in assignments:
        add(
            a.due_date.date(), f"Due: {a.title}", "coral" if a.is_exam else "amber",
            assignment_url(a) if assignment_url else None,
        )

    return day_map
