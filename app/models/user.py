from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.constants import ROLES, ROLE_TEACHER, ROLE_STUDENT
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    is_active_flag = db.Column("is_active", db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    teacher_profile = db.relationship(
        "TeacherProfile", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    student_profile = db.relationship(
        "StudentProfile", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (db.CheckConstraint(role.in_(ROLES), name="ck_users_role"),)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self):
        return self.is_active_flag

    @property
    def is_teacher(self):
        return self.role == ROLE_TEACHER

    @property
    def is_student(self):
        return self.role == ROLE_STUDENT

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class TeacherProfile(db.Model):
    __tablename__ = "teacher_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    department = db.Column(db.String(120))
    title = db.Column(db.String(120))


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    grade_level = db.Column(db.String(40))
    student_number = db.Column(db.String(40))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
