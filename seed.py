import os
import shutil
import wave
from datetime import time, datetime, timedelta, timezone

from flask import current_app

from app.extensions import db
from app.models.user import User, TeacherProfile, StudentProfile
from app.models.academic import Subject, ClassGroup, Enrollment, Timetable
from app.models.worksheet import Worksheet, WorksheetElement
from app.models.assignment import Assignment, Submission, StudentAnswer, ModelAnswer, VoiceFeedback
from app.models.notification import Announcement, Notification
from app.models.calendar_event import CalendarEvent
from app.models.storybook import Storybook, StorybookPage
from app.models.canvas import CanvasStroke, StickyNote
from app.models.textbook import Textbook, TextbookNote, TextbookPageAnnotation
from app.models.group_collab import (
    ProjectGroup,
    ProjectGroupMembership,
    GroupComment,
    GroupDocument,
    GroupDocumentRevision,
    GroupMessage,
)
from app.services import canvas_service


def run_seed():
    db.drop_all()
    db.create_all()

    teacher = User(email="teacher@ultraedu.app", role="teacher", full_name="Ms. Tan")
    teacher.set_password("teacher123")
    db.session.add(teacher)

    # A second teacher account owns every other subject's classes, so the demo
    # teacher account (Ms. Tan) only ever sees her own — Mathematics — on her
    # dashboard and timetable, not the whole school's schedule.
    other_teacher = User(email="teacher2@ultraedu.app", role="teacher", full_name="Mr. Wong")
    other_teacher.set_password("teacher123")
    db.session.add(other_teacher)

    student = User(email="student@ultraedu.app", role="student", full_name="Alex Lim")
    student.set_password("student123")
    db.session.add(student)

    # A second student, used for group-project pairing (shared documents, comments,
    # file sharing, teammate chat) alongside Alex Lim.
    student2 = User(email="student2@ultraedu.app", role="student", full_name="Priya Nair")
    student2.set_password("student123")
    db.session.add(student2)

    db.session.flush()

    db.session.add(TeacherProfile(user_id=teacher.id, department="Mathematics", title="Class Teacher"))
    db.session.add(TeacherProfile(user_id=other_teacher.id, department="General", title="Subject Teacher"))
    db.session.add(StudentProfile(user_id=student.id, grade_level="Primary 5", student_number="P5-014"))
    db.session.add(StudentProfile(user_id=student2.id, grade_level="Primary 5", student_number="P5-015"))

    subjects = {
        "MATH": Subject(name="Mathematics", code="MATH", color_hex="#3f6f5f"),
        "ENG": Subject(name="English", code="ENG", color_hex="#a15c3e"),
        "CHI": Subject(name="Chinese", code="CHI", color_hex="#8a4b8f"),
        "SCI": Subject(name="Science", code="SCI", color_hex="#3a6ea5"),
        "PE": Subject(name="Physical Education", code="PE", color_hex="#e0685a"),
        "ART": Subject(name="Art", code="ART", color_hex="#c2569c"),
        "COMP": Subject(name="Computing", code="COMP", color_hex="#4a5fd1"),
        "SOC": Subject(name="Social Studies", code="SOC", color_hex="#6b8e23"),
        "MUS": Subject(name="Music", code="MUS", color_hex="#cc6b49"),
        "CCE": Subject(name="Character & Citizenship Education", code="CCE", color_hex="#2f8f7a"),
        "ASSEMBLY": Subject(name="Morning Assembly", code="ASSEMBLY", color_hex="#999999"),
        "RECESS": Subject(name="Recess", code="RECESS", color_hex="#bbbbbb"),
        "DISMISSAL": Subject(name="Dismissal", code="DISMISSAL", color_hex="#888888"),
    }
    for s in subjects.values():
        db.session.add(s)
    db.session.flush()

    class_group = ClassGroup(
        name="Primary 5 Math A",
        subject_id=subjects["MATH"].id,
        teacher_id=teacher.id,
        academic_year="2026",
    )
    db.session.add(class_group)
    db.session.flush()

    db.session.add(Enrollment(class_group_id=class_group.id, student_id=student.id))
    db.session.add(Enrollment(class_group_id=class_group.id, student_id=student2.id))

    # One ClassGroup per subject block on the weekly timetable, so the full school-week
    # schedule below has somewhere to attach. All non-Mathematics classes (and the
    # non-teaching blocks) belong to `other_teacher`, not Ms. Tan — she should only ever
    # see her own Mathematics class. Reuses `class_group` (Primary 5 Math A) for
    # Mathematics since assignments/worksheets are already linked to it.
    class_groups_by_code = {"MATH": class_group}
    other_class_names = {
        "ENG": "Primary 5 English",
        "CHI": "Primary 5 Chinese",
        "SCI": "Primary 5 Science",
        "PE": "Primary 5 Physical Education",
        "ART": "Primary 5 Art",
        "COMP": "Primary 5 Computing",
        "SOC": "Primary 5 Social Studies",
        "MUS": "Primary 5 Music",
        "CCE": "Primary 5 Character & Citizenship Education",
        "ASSEMBLY": "Morning Assembly",
        "RECESS": "Recess",
        "DISMISSAL": "Dismissal",
    }
    for code, name in other_class_names.items():
        cg = ClassGroup(
            name=name, subject_id=subjects[code].id, teacher_id=other_teacher.id, academic_year="2026",
        )
        db.session.add(cg)
        class_groups_by_code[code] = cg
    db.session.flush()

    for code, cg in class_groups_by_code.items():
        if code != "MATH":
            db.session.add(Enrollment(class_group_id=cg.id, student_id=student.id))
            db.session.add(Enrollment(class_group_id=cg.id, student_id=student2.id))

    # Full weekly timetable (Monday=0 .. Friday=4), matching the school's example schedule.
    periods = [
        (1, time(7, 45), time(8, 15), ["ASSEMBLY"] * 5),
        (2, time(8, 15), time(9, 15), ["ENG", "MATH", "SCI", "ENG", "CHI"]),
        (3, time(9, 15), time(10, 15), ["MATH", "SCI", "ENG", "MATH", "SCI"]),
        (4, time(10, 15), time(10, 45), ["RECESS"] * 5),
        (5, time(10, 45), time(11, 45), ["CHI", "ENG", "MATH", "CHI", "PE"]),
        (6, time(11, 45), time(12, 45), ["SCI", "ART", "COMP", "SOC", "MATH"]),
        (7, time(12, 45), time(13, 30), ["PE", "CHI", "MUS", "CCE", "DISMISSAL"]),
    ]
    timetable_rows = []
    for period_number, start, end, week_codes in periods:
        for day_of_week, code in enumerate(week_codes):
            timetable_rows.append(
                Timetable(
                    class_group_id=class_groups_by_code[code].id,
                    day_of_week=day_of_week,
                    period_number=period_number,
                    start_time=start,
                    end_time=end,
                )
            )
    db.session.add_all(timetable_rows)

    worksheet = Worksheet(
        title="Fractions Practice",
        teacher_id=teacher.id,
        subject_id=subjects["MATH"].id,
        description="Warm-up worksheet on equivalent fractions.",
    )
    db.session.add(worksheet)
    db.session.flush()

    mcq_element = WorksheetElement(
        worksheet_id=worksheet.id,
        element_type="multiple_choice",
        page_number=1,
        order_index=0,
        x=40,
        y=40,
        width=400,
        height=150,
        prompt_text="Which fraction is equivalent to 1/2?",
        points=1,
        config_json={
            "options": [
                {"id": "a", "text": "2/4"},
                {"id": "b", "text": "1/3"},
                {"id": "c", "text": "3/5"},
            ],
            "correct_option_id": "a",
        },
    )
    fill_blank_element = WorksheetElement(
        worksheet_id=worksheet.id,
        element_type="fill_blank",
        page_number=1,
        order_index=1,
        x=40,
        y=220,
        width=400,
        height=190,
        prompt_text="3/4 of a pizza is the same as ___/8 of a pizza.",
        points=1,
        config_json={"correct_text": "6", "case_sensitive": False},
    )
    handwriting_element = WorksheetElement(
        worksheet_id=worksheet.id,
        element_type="handwriting_area",
        page_number=1,
        order_index=2,
        x=40,
        y=430,
        width=650,
        height=320,
        prompt_text="Show your working for: simplify 8/12 to its lowest terms.",
        points=2,
        config_json={"ruled": True},
    )
    db.session.add_all([mcq_element, fill_blank_element, handwriting_element])

    assignment = Assignment(
        title="Fractions Homework",
        description="Practice worksheet on equivalent fractions and simplifying.",
        class_group_id=class_group.id,
        teacher_id=teacher.id,
        subject_id=subjects["MATH"].id,
        assignment_type="worksheet",
        worksheet_id=worksheet.id,
        difficulty="easy",
        ai_mode="hints_only",
        max_score=4,
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        published_at=datetime.now(timezone.utc),
    )
    db.session.add(assignment)

    announcement = Announcement(
        teacher_id=teacher.id,
        class_group_id=class_group.id,
        subject_id=subjects["MATH"].id,
        title="Welcome to Term 3",
        body="Looking forward to a great term of fractions and long division!",
        announcement_type="general",
    )
    db.session.add(announcement)

    db.session.flush()

    db.session.add(
        Notification(
            user_id=student.id,
            type="new_assignment",
            title=f"New assignment: {assignment.title}",
            body=assignment.description,
        )
    )

    # --- Model answers: shown only to the teacher while grading ---
    handwriting_model_doc = canvas_service.create_document(
        "model_answer", teacher.id, int(handwriting_element.width), int(handwriting_element.height)
    )
    db.session.add_all(
        [
            CanvasStroke(
                canvas_document_id=handwriting_model_doc.id, author_id=teacher.id, layer="base",
                tool="pen", color="#1a1a1a", width=3, sequence=0,
                points_json={"points": [{"x": 40, "y": 60, "t": 0}, {"x": 200, "y": 60, "t": 120}]},
            ),
            CanvasStroke(
                canvas_document_id=handwriting_model_doc.id, author_id=teacher.id, layer="base",
                tool="pen", color="#1a1a1a", width=3, sequence=1,
                points_json={"points": [{"x": 40, "y": 130, "t": 0}, {"x": 160, "y": 130, "t": 100}]},
            ),
        ]
    )
    db.session.add_all(
        [
            ModelAnswer(
                assignment_id=assignment.id,
                worksheet_element_id=fill_blank_element.id,
                text_notes="Look for the multiplier from 4 to 8 (×2), then apply it to the numerator: 3 × 2 = 6.",
            ),
            ModelAnswer(
                assignment_id=assignment.id,
                worksheet_element_id=handwriting_element.id,
                canvas_document_id=handwriting_model_doc.id,
                text_notes="8/12 → divide top and bottom by their GCF (4) → 2/3. Full marks for showing the division step.",
            ),
        ]
    )

    # --- Example submission #1: Alex Lim submitted, was graded, and was sent back for
    # corrections with written AND voice feedback — demonstrates the full return/return-
    # for-corrections/voice-feedback flow described by the teacher. ---
    alex_submission = Submission(
        assignment_id=assignment.id,
        student_id=student.id,
        status="needs_revision",
        started_at=datetime.now(timezone.utc) - timedelta(days=1),
        submitted_at=datetime.now(timezone.utc) - timedelta(hours=20),
        score=2,
        max_score=assignment.max_score,
        feedback_text=(
            "Nice work on question 1! For question 2, double-check your multiplier — "
            "listen to my voice note for a walkthrough. Please redo the handwriting "
            "working for question 3 showing every step, then resubmit."
        ),
        graded_by=teacher.id,
        graded_at=datetime.now(timezone.utc) - timedelta(hours=19),
    )
    db.session.add(alex_submission)
    db.session.flush()

    alex_fill_blank_doc = canvas_service.create_document(
        "student_answer", student.id, int(fill_blank_element.width), int(fill_blank_element.height)
    )
    alex_fill_blank_doc.is_locked = False
    alex_handwriting_doc = canvas_service.create_document(
        "student_answer", student.id, int(handwriting_element.width), int(handwriting_element.height)
    )
    alex_handwriting_doc.is_locked = False
    db.session.add_all(
        [
            StudentAnswer(
                submission_id=alex_submission.id, worksheet_element_id=mcq_element.id,
                answer_json={"selected_option_id": "a"},
            ),
            StudentAnswer(
                submission_id=alex_submission.id, worksheet_element_id=fill_blank_element.id,
                canvas_document_id=alex_fill_blank_doc.id,
            ),
            StudentAnswer(
                submission_id=alex_submission.id, worksheet_element_id=handwriting_element.id,
                canvas_document_id=alex_handwriting_doc.id,
            ),
        ]
    )
    db.session.add_all(
        [
            CanvasStroke(
                canvas_document_id=alex_fill_blank_doc.id, author_id=student.id, layer="base",
                tool="pen", color="#1a1a1a", width=2.5, sequence=0,
                points_json={"points": [{"x": 30, "y": 50, "t": 0}, {"x": 55, "y": 55, "t": 90}, {"x": 45, "y": 90, "t": 180}]},
            ),
            CanvasStroke(
                canvas_document_id=alex_handwriting_doc.id, author_id=student.id, layer="base",
                tool="pen", color="#1a1a1a", width=2.5, sequence=0,
                points_json={"points": [{"x": 30, "y": 40, "t": 0}, {"x": 180, "y": 45, "t": 150}]},
            ),
            CanvasStroke(
                canvas_document_id=alex_handwriting_doc.id, author_id=teacher.id, layer="annotation",
                tool="highlighter", color="#e0a530", width=10, sequence=1,
                points_json={"points": [{"x": 25, "y": 40, "t": 0}, {"x": 190, "y": 45, "t": 60}]},
            ),
        ]
    )

    voice_feedback_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "MATH")
    os.makedirs(voice_feedback_dir, exist_ok=True)
    voice_feedback_filename = "seed_voice_feedback_alex.wav"
    voice_feedback_path = os.path.join(voice_feedback_dir, voice_feedback_filename)
    with wave.open(voice_feedback_path, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)
        wav_file.writeframes(b"\x00\x00" * 8000 * 2)  # 2 seconds of silence
    db.session.add(
        VoiceFeedback(
            submission_id=alex_submission.id,
            audio_file_path=f"MATH/{voice_feedback_filename}",
            duration_seconds=2,
            recorded_by=teacher.id,
            recorded_at=datetime.now(timezone.utc) - timedelta(hours=19),
        )
    )
    db.session.add(
        Notification(
            user_id=student.id,
            type="revision_requested",
            title=f"Corrections needed on {assignment.title}",
            body=alex_submission.feedback_text,
        )
    )

    # --- Example submission #2: Priya Nair just submitted — sitting in the teacher's
    # grading queue, ready to be marked (with the model answers above alongside it). ---
    priya_submission = Submission(
        assignment_id=assignment.id,
        student_id=student2.id,
        status="submitted",
        started_at=datetime.now(timezone.utc) - timedelta(hours=3),
        submitted_at=datetime.now(timezone.utc) - timedelta(minutes=40),
        max_score=assignment.max_score,
    )
    db.session.add(priya_submission)
    db.session.flush()

    priya_fill_blank_doc = canvas_service.create_document(
        "student_answer", student2.id, int(fill_blank_element.width), int(fill_blank_element.height)
    )
    priya_fill_blank_doc.is_locked = True
    priya_handwriting_doc = canvas_service.create_document(
        "student_answer", student2.id, int(handwriting_element.width), int(handwriting_element.height)
    )
    priya_handwriting_doc.is_locked = True
    db.session.add_all(
        [
            StudentAnswer(
                submission_id=priya_submission.id, worksheet_element_id=mcq_element.id,
                answer_json={"selected_option_id": "a"},
            ),
            StudentAnswer(
                submission_id=priya_submission.id, worksheet_element_id=fill_blank_element.id,
                canvas_document_id=priya_fill_blank_doc.id,
            ),
            StudentAnswer(
                submission_id=priya_submission.id, worksheet_element_id=handwriting_element.id,
                canvas_document_id=priya_handwriting_doc.id,
            ),
        ]
    )
    db.session.add_all(
        [
            CanvasStroke(
                canvas_document_id=priya_fill_blank_doc.id, author_id=student2.id, layer="base",
                tool="pen", color="#1a1a1a", width=2.5, sequence=0,
                points_json={"points": [{"x": 30, "y": 50, "t": 0}, {"x": 60, "y": 90, "t": 100}]},
            ),
            CanvasStroke(
                canvas_document_id=priya_handwriting_doc.id, author_id=student2.id, layer="base",
                tool="pen", color="#1a1a1a", width=2.5, sequence=0,
                points_json={"points": [{"x": 30, "y": 40, "t": 0}, {"x": 200, "y": 90, "t": 200}]},
            ),
        ]
    )
    db.session.add(
        Notification(
            user_id=teacher.id,
            type="submission_received",
            title=f"{student2.full_name} submitted {assignment.title}",
            body=None,
        )
    )

    # --- Group project: Alex Lim and Priya Nair team up on a poster assignment ---
    group_assignment = Assignment(
        title="Class Poster: Fractions in Real Life",
        description="Work with your teammate to design a poster showing three real-life uses of fractions.",
        class_group_id=class_group.id,
        teacher_id=teacher.id,
        subject_id=subjects["MATH"].id,
        assignment_type="file_upload",
        difficulty="medium",
        ai_mode="disabled",
        is_group_assignment=True,
        allow_file_attachment=True,
        max_score=10,
        due_date=datetime.now(timezone.utc) + timedelta(days=10),
        published_at=datetime.now(timezone.utc),
    )
    db.session.add(group_assignment)
    db.session.flush()

    project_group = ProjectGroup(assignment_id=group_assignment.id, name="Team Fraction")
    db.session.add(project_group)
    db.session.flush()

    db.session.add_all(
        [
            ProjectGroupMembership(group_id=project_group.id, student_id=student.id, is_leader=True),
            ProjectGroupMembership(group_id=project_group.id, student_id=student2.id),
        ]
    )

    group_document = GroupDocument(
        group_id=project_group.id,
        title="Shared Document",
        content=(
            "Poster plan:\n"
            "1. Fractions in cooking — measuring ingredients\n"
            "2. Fractions in sharing — splitting a pizza\n"
            "3. Fractions in time — quarter past, half past\n"
        ),
        updated_by_id=student.id,
    )
    db.session.add(group_document)
    db.session.flush()
    db.session.add(
        GroupDocumentRevision(
            document_id=group_document.id, student_id=student.id, content=group_document.content,
        )
    )
    db.session.add(
        GroupComment(
            group_id=project_group.id, student_id=student2.id,
            body="I can draw the pizza-sharing diagram tonight!",
        )
    )
    db.session.add_all(
        [
            GroupMessage(group_id=project_group.id, student_id=student.id, body="Hey! I started our plan in the shared doc."),
            GroupMessage(group_id=project_group.id, student_id=student2.id, body="Nice, I'll add the cooking example."),
        ]
    )
    db.session.add(
        Notification(
            user_id=student2.id,
            type="new_assignment",
            title=f"New assignment: {group_assignment.title}",
            body=group_assignment.description,
        )
    )

    # --- Example examination: a draft, ready for the teacher to publish (which
    # automatically turns on Exam Mode for the class and keeps AI hints off). ---
    examination = Assignment(
        title="Mid-Term Fractions Quiz",
        description="A short, timed quiz covering equivalent fractions and simplifying.",
        class_group_id=class_group.id,
        teacher_id=teacher.id,
        subject_id=subjects["MATH"].id,
        assignment_type="worksheet",
        worksheet_id=worksheet.id,
        difficulty="medium",
        ai_mode="disabled",
        is_exam=True,
        max_score=4,
        due_date=datetime.now(timezone.utc) + timedelta(days=3),
    )
    db.session.add(examination)

    today = datetime.now().date()
    db.session.add(
        CalendarEvent(
            title="Sports Day",
            description="Annual school sports day — all classes.",
            event_type="school_event",
            start_date=today + timedelta(days=6),
            end_date=today + timedelta(days=6),
            class_group_id=None,
            created_by=teacher.id,
        )
    )
    db.session.add(
        CalendarEvent(
            title="Mid-Term Break",
            description="No lessons this week.",
            event_type="holiday",
            start_date=today + timedelta(days=14),
            end_date=today + timedelta(days=18),
            class_group_id=None,
            created_by=teacher.id,
        )
    )

    # --- English Storybook: "The Secret Garden Key" ---
    eng_worksheet = Worksheet(
        title="The Secret Garden Key — Activities",
        teacher_id=teacher.id,
        subject_id=subjects["ENG"].id,
        description="Comprehension, vocabulary, and highlighting activities.",
    )
    db.session.add(eng_worksheet)
    db.session.flush()

    highlight_passage = (
        "Sophie tended to the neglected plants every day. "
        "She watered them gently and pulled out the weeds. "
        "She learned about responsibility, kindness, and caring for nature. "
        "The garden slowly came back to life"
    )
    db.session.add_all(
        [
            WorksheetElement(
                worksheet_id=eng_worksheet.id,
                element_type="multiple_choice",
                page_number=1,
                order_index=0,
                x=40, y=40, width=450, height=150,
                prompt_text="Comprehension: What did Sophie find hidden inside an old book?",
                points=1,
                config_json={
                    "options": [
                        {"id": "a", "text": "A golden key"},
                        {"id": "b", "text": "A silver coin"},
                        {"id": "c", "text": "A map"},
                    ],
                    "correct_option_id": "a",
                },
            ),
            WorksheetElement(
                worksheet_id=eng_worksheet.id,
                element_type="matching",
                page_number=1,
                order_index=1,
                x=40, y=220, width=450, height=200,
                prompt_text="Vocabulary support: match each word to its meaning.",
                points=3,
                config_json={
                    "left": [
                        {"id": "l1", "text": "mysterious"},
                        {"id": "l2", "text": "tarnished"},
                        {"id": "l3", "text": "neglected"},
                    ],
                    "right": [
                        {"id": "r1", "text": "strange and hard to explain"},
                        {"id": "r2", "text": "dulled or discoloured by age"},
                        {"id": "r3", "text": "not cared for"},
                    ],
                    "correct_pairs": {"l1": "r1", "l2": "r2", "l3": "r3"},
                },
            ),
            WorksheetElement(
                worksheet_id=eng_worksheet.id,
                element_type="text_highlight",
                page_number=1,
                order_index=2,
                x=40, y=440, width=650, height=220,
                prompt_text="Highlight the sentence that shows what Sophie learned in the garden.",
                points=1,
                config_json={"passage": highlight_passage, "correct_sentence_ids": ["s3"]},
            ),
        ]
    )

    eng_storybook = Storybook(
        title="The Secret Garden Key",
        language="english",
        subject_id=subjects["ENG"].id,
        description=(
            "Sophie discovers a mysterious golden key hidden inside an old book. "
            "It unlocks a forgotten garden where she learns about responsibility, "
            "kindness, and caring for nature."
        ),
        worksheet_id=eng_worksheet.id,
        ai_mode="hints_only",
        created_by=teacher.id,
    )
    db.session.add(eng_storybook)
    db.session.flush()

    db.session.add_all(
        [
            StorybookPage(
                storybook_id=eng_storybook.id, page_number=1,
                text_content=(
                    "Sophie discovered a mysterious golden key hidden inside an old book on a "
                    "rainy afternoon. The key was small, tarnished with age, and etched with "
                    "strange leaf patterns she had never seen before."
                ),
            ),
            StorybookPage(
                storybook_id=eng_storybook.id, page_number=2,
                text_content=(
                    "Curious, she followed a narrow path behind her grandmother's cottage until "
                    "she found a rusted gate, locked tight. With trembling hands, she slid the "
                    "key into the lock — and it turned with a soft click."
                ),
            ),
            StorybookPage(
                storybook_id=eng_storybook.id, page_number=3,
                text_content=(
                    "Beyond the gate lay a forgotten garden, wild and overgrown. As Sophie tended "
                    "to the neglected plants day after day, she learned about responsibility, "
                    "kindness, and caring for nature — lessons that would stay with her long "
                    "after the garden bloomed again."
                ),
            ),
        ]
    )

    # --- Chinese Storybook: 《小树苗长大了》 ---
    chi_worksheet = Worksheet(
        title="《小树苗长大了》活动",
        teacher_id=teacher.id,
        subject_id=subjects["CHI"].id,
        description="生字、拼音与阅读理解活动。",
    )
    db.session.add(chi_worksheet)
    db.session.flush()

    db.session.add_all(
        [
            WorksheetElement(
                worksheet_id=chi_worksheet.id,
                element_type="fill_blank",
                page_number=1,
                order_index=0,
                x=40, y=40, width=450, height=190,
                prompt_text="生字学习：小树苗最终长成了一棵____。",
                points=1,
                config_json={"correct_text": "大树", "case_sensitive": False},
            ),
            WorksheetElement(
                worksheet_id=chi_worksheet.id,
                element_type="fill_blank",
                page_number=1,
                order_index=1,
                x=40, y=250, width=450, height=190,
                prompt_text="拼音：「发芽」的拼音是？",
                points=1,
                config_json={"correct_text": "fa ya", "case_sensitive": False},
            ),
            WorksheetElement(
                worksheet_id=chi_worksheet.id,
                element_type="multiple_choice",
                page_number=1,
                order_index=2,
                x=40, y=460, width=450, height=150,
                prompt_text="阅读理解：小树苗在成长过程中学会了什么？",
                points=1,
                config_json={
                    "options": [
                        {"id": "a", "text": "坚持和分享"},
                        {"id": "b", "text": "唱歌跳舞"},
                        {"id": "c", "text": "游泳追逐"},
                    ],
                    "correct_option_id": "a",
                },
            ),
        ]
    )

    chi_storybook = Storybook(
        title="《小树苗长大了》",
        language="chinese",
        subject_id=subjects["CHI"].id,
        description="春天来了，小树苗刚刚发芽。每天，太阳给它温暖，雨水滋润着它，鸟儿陪伴着它成长。经过四季的变化，小树苗终于长成了一棵大树，学会了坚持和分享。",
        worksheet_id=chi_worksheet.id,
        ai_mode="hints_only",
        created_by=teacher.id,
    )
    db.session.add(chi_storybook)
    db.session.flush()

    db.session.add_all(
        [
            StorybookPage(
                storybook_id=chi_storybook.id, page_number=1,
                text_content="春天来了，小树苗刚刚发芽。嫩绿的叶子在风中轻轻摇摆，好像在跟世界打招呼。",
            ),
            StorybookPage(
                storybook_id=chi_storybook.id, page_number=2,
                text_content="每天，太阳给它温暖，雨水滋润着它，鸟儿陪伴着它成长。小树苗努力地向下扎根，向上生长。",
            ),
            StorybookPage(
                storybook_id=chi_storybook.id, page_number=3,
                text_content="经过四季的变化，小树苗终于长成了一棵大树，学会了坚持和分享。它为鸟儿提供家园，为路人提供阴凉。",
            ),
        ]
    )

    # --- Example textbook: an original Primary 5 Science coursebook (generated for
    # UltraEdu, no copyrighted material) with pre-made handwriting, a highlight, an
    # underline, a shape, and a sticky note on the Chapter 1 page, plus one example note.
    # The PDF itself is committed at app/static/sample_content/ (see app/pdf_generators.py
    # for how it was produced) and copied into place here, so `flask seed` always has a
    # real file to point at, in any environment, with no runtime PDF-generation step.
    sci_textbook_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "SCI")
    os.makedirs(sci_textbook_dir, exist_ok=True)
    sci_textbook_filename = "p5_science_coursebook.pdf"
    sci_textbook_source = os.path.join(
        current_app.root_path, "static", "sample_content", "p5_science_coursebook.pdf"
    )
    shutil.copyfile(sci_textbook_source, os.path.join(sci_textbook_dir, sci_textbook_filename))

    sci_textbook = Textbook(
        title="Primary 5 Science Coursebook",
        description="An 8-chapter Primary 5 Science coursebook — practice reading, then mark it up right on the page.",
        subject_id=subjects["SCI"].id,
        class_group_id=class_groups_by_code["SCI"].id,
        file_path=f"SCI/{sci_textbook_filename}",
        uploaded_by=other_teacher.id,
        published_at=datetime.now(timezone.utc),
    )
    db.session.add(sci_textbook)
    db.session.flush()

    # Sized to match this PDF's actual A4 page aspect ratio (595x842pt) at the reader's
    # 800px target width, so the seeded ink lines up exactly with the rendered page.
    textbook_page_doc = canvas_service.create_document("textbook_page", student.id, 800, 1131)
    db.session.add_all(
        [
            CanvasStroke(
                # Underline under the "Chapter 1" heading
                canvas_document_id=textbook_page_doc.id, author_id=student.id, layer="base",
                tool="pen", color="#1a1a1a", width=2.5, sequence=0,
                points_json={"points": [{"x": 114, "y": 156, "t": 0}, {"x": 500, "y": 156, "t": 120}]},
            ),
            CanvasStroke(
                # Highlight over the intro sentence
                canvas_document_id=textbook_page_doc.id, author_id=student.id, layer="base",
                tool="highlighter", color="#fff3b0", width=16, sequence=1,
                points_json={"points": [{"x": 76, "y": 210, "t": 0}, {"x": 740, "y": 210, "t": 100}]},
            ),
            CanvasStroke(
                # Underline under the "Characteristics of living things" subheading
                canvas_document_id=textbook_page_doc.id, author_id=student.id, layer="base",
                tool="line", color="#b3403a", width=2, sequence=2,
                points_json={"points": [{"x": 76, "y": 268, "t": 0}, {"x": 330, "y": 268, "t": 80}]},
            ),
            CanvasStroke(
                # Rectangle framing the Living / Non-living comparison diagram
                canvas_document_id=textbook_page_doc.id, author_id=student.id, layer="base",
                tool="rectangle", color="#4a5fd1", width=2, sequence=3,
                points_json={"points": [{"x": 68, "y": 775, "t": 0}, {"x": 730, "y": 908, "t": 90}]},
            ),
        ]
    )
    db.session.add(
        StickyNote(
            canvas_document_id=textbook_page_doc.id, author_id=student.id,
            x=540, y=160, width=200, height=100,
            text="Key idea: living things GROW, need FOOD, and can MOVE!", color="#fff3b0",
        )
    )
    db.session.add(
        TextbookPageAnnotation(
            textbook_id=sci_textbook.id, student_id=student.id,
            page_number=3, canvas_document_id=textbook_page_doc.id,
        )
    )
    db.session.add(
        TextbookNote(
            textbook_id=sci_textbook.id, student_id=student.id, page_number=3,
            body="Living things need food, water and air — and they can grow, move, and reproduce. Remember this for the quiz!",
        )
    )

    db.session.commit()

    return {
        "teacher": teacher,
        "other_teacher": other_teacher,
        "student": student,
        "student2": student2,
        "class_group": class_group,
        "subjects": subjects,
        "worksheet": worksheet,
        "assignment": assignment,
        "group_assignment": group_assignment,
        "storybooks": [eng_storybook, chi_storybook],
    }
