from datetime import datetime, timezone

from app.extensions import db


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    color_hex = db.Column(db.String(7), default="#3f6f5f")

    def __repr__(self):
        return f"<Subject {self.code}>"

    @classmethod
    def academic_query(cls):
        """Excludes non-teaching timetable blocks (assembly/recess/dismissal) — use this
        instead of Subject.query wherever a human picks a subject for content they're
        creating (worksheets, resources, storybooks, textbooks, etc.)."""
        from app.constants import NON_ACADEMIC_SUBJECT_CODES

        return cls.query.filter(cls.code.notin_(NON_ACADEMIC_SUBJECT_CODES))

    @property
    def is_academic(self):
        from app.constants import NON_ACADEMIC_SUBJECT_CODES

        return self.code not in NON_ACADEMIC_SUBJECT_CODES


class ClassGroup(db.Model):
    __tablename__ = "class_groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    academic_year = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    subject = db.relationship("Subject")
    teacher = db.relationship("User")
    enrollments = db.relationship("Enrollment", backref="class_group", cascade="all, delete-orphan")
    timetable_entries = db.relationship(
        "Timetable", backref="class_group", cascade="all, delete-orphan"
    )

    @property
    def student_ids(self):
        return [e.student_id for e in self.enrollments]


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True)
    class_group_id = db.Column(db.Integer, db.ForeignKey("class_groups.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    student = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("class_group_id", "student_id", name="uq_enrollment_class_student"),
    )


class Timetable(db.Model):
    __tablename__ = "timetable_entries"

    id = db.Column(db.Integer, primary_key=True)
    class_group_id = db.Column(db.Integer, db.ForeignKey("class_groups.id"), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday .. 6=Sunday
    period_number = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room = db.Column(db.String(40))

    __table_args__ = (
        db.CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_timetable_day"),
    )
