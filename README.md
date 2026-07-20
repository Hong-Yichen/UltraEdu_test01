# UltraEdu

A paperless learning platform where students complete work by **handwriting and drawing
directly on digital worksheets** (mouse, touch, or stylus) instead of typing. Built with
Flask + SQLAlchemy + vanilla JS (no frontend framework, no build step).

## Features in this build

- Teacher / student accounts with role-based access
- Class timetables and dashboards
- A worksheet builder: multiple-choice, fill-in-the-blank, matching, label-the-diagram,
  drawing areas, handwriting areas, image upload, and text-highlight question types
- A from-scratch handwriting/drawing canvas engine (pen, highlighter, eraser), with a
  teacher "overlay" mode that lets a teacher annotate directly on top of a student's
  submitted work without ever altering the student's original ink
- Full assignment lifecycle: create → publish → take → submit → grade → feedback
- Resources ("digital file cabinet"), announcements, and in-app notifications (polled)
- Storybooks (English/Chinese) that reuse the worksheet engine for comprehension activities
- Group projects (group creation, shared files, comments)
- Bookmarks, a homework planner, and a student progress dashboard
- Teacher analytics (class average, completion rate, grade distribution)
- An AI hint toggle per assignment/storybook — wired end-to-end but returns a canned,
  type-aware hint (see `app/services/ai_hints.py`) rather than calling a live model yet
- Exam Mode and Classroom Lockdown, enforced **server-side** (not just hidden in the UI)
- A school calendar (month-grid view) — teachers create school-wide or class-specific
  events, students see a read-only view; assignment due dates are auto-overlaid
- Direct messaging between a student and their teacher(s) — 1:1 only, no student-to-student
  chat, enforced by only allowing threads between a student and a teacher of one of their
  actual classes (see `app/services/messaging_service.py`); polling-based, no WebSockets
- Digital textbooks — teachers upload a PDF (school-wide or class-specific), students read
  it in an in-browser viewer and take their own page-referenced notes alongside it

### Explicitly out of scope for this build

- A live AI call (the hint endpoint has one clean seam to swap in later)
- Voice feedback recording/playback (DB field stub only, no recording UI)
- Offline/PWA sync and video hosting

## Try it in your browser with GitHub Codespaces

No local install needed — on the repo's GitHub page, click **Code → Codespaces → Create
codespace**. It provisions a container and installs dependencies automatically
(`.devcontainer/devcontainer.json`). Once it's ready, open a terminal in the codespace and run:

```bash
export FLASK_APP=wsgi.py
flask seed
flask run --host=0.0.0.0
```

Codespaces will pop up a "forwarded port" notification/toast for port 5000 — click it (or
open the **Ports** tab) to load the app in a new browser tab. Use `--host=0.0.0.0` (not the
default `127.0.0.1`) so the forwarded port can actually reach the dev server.

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit SECRET_KEY etc. if needed
```

## Running locally

For local development, the fastest path is the seed command — it (re)creates the schema
directly from the current models and populates demo data, bypassing Alembic migrations
entirely:

```bash
export FLASK_APP=wsgi.py        # Windows: set FLASK_APP=wsgi.py
flask seed
flask run
```

Demo accounts (seeded):

| Role    | Email                       | Password    | Notes                                    |
|---------|-----------------------------|--------------|-------------------------------------------|
| Teacher | teacher@ultraedu.app        | teacher123   | Ms. Tan — teaches Mathematics only        |
| Teacher | teacher2@ultraedu.app       | teacher123   | Mr. Wong — teaches every other subject    |
| Student | student@ultraedu.app        | student123   | Alex Lim — enrolled in the full timetable |
| Student | student2@ultraedu.app       | student123   | Priya Nair — Alex's group project teammate |

Each teacher only ever sees their own classes/timetable on their dashboard — the two
accounts exist so the demo's full weekly timetable (which spans many subjects) has a
realistic owner for each class, rather than one teacher account appearing to teach
every subject in the school.

## Production-style migrations

A migration history is tracked separately under `migrations/` for deployments that need
real schema upgrades instead of a full reset:

```bash
flask db upgrade
```

Note: `flask seed`'s `drop_all`/`create_all` and Alembic's version tracking are two
independent paths — don't mix them against the same database file. Pick one workflow
per environment (`flask seed` for local dev/demo, `flask db upgrade` for anything you
want to preserve data in).

## Project layout

```
app/
  models/       SQLAlchemy models, one module per domain area
  blueprints/   auth / main / teacher / student / api — routes only, thin
  services/     business logic (canvas persistence, exam/lockdown guards, file storage,
                notifications, AI hint seam) — reused across blueprints
  templates/    Jinja templates, mirrors the blueprint structure
  static/       css/ (paper + worksheet styling) and js/ (canvas engine, autosave,
                worksheet builder, notification polling)
seed.py         demo data for `flask seed`
wsgi.py         entry point
```

See `app/services/canvas_service.py` and `app/static/js/canvas.js` for the core
handwriting engine, and `app/services/exam_lockdown_guard.py` for how Exam Mode /
Lockdown Mode are enforced server-side via `student_bp.before_request`.
