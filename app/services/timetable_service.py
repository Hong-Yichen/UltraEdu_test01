from app.models.academic import Timetable

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def build_week_grid(class_ids):
    """Returns (periods, grid) for a Mon-Fri timetable grid.

    periods: sorted list of distinct (period_number, start_time, end_time).
    grid: {period_number: {day_of_week: Timetable}} for day_of_week in 0..4.
    """
    if not class_ids:
        return [], {}

    entries = (
        Timetable.query.filter(
            Timetable.class_group_id.in_(class_ids), Timetable.day_of_week <= 4
        )
        .order_by(Timetable.period_number)
        .all()
    )

    periods_by_number = {}
    grid = {}
    for entry in entries:
        periods_by_number[entry.period_number] = (entry.start_time, entry.end_time)
        grid.setdefault(entry.period_number, {})[entry.day_of_week] = entry

    periods = [
        (number, start, end)
        for number, (start, end) in sorted(periods_by_number.items())
    ]
    return periods, grid
