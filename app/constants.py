ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"
ROLES = (ROLE_TEACHER, ROLE_STUDENT)

# Subject codes used to hang non-teaching timetable blocks (assembly, recess, dismissal)
# off the same ClassGroup/Timetable schema as real subjects. They belong on the daily
# schedule but should be excluded from "your subjects/classes" style listings.
NON_ACADEMIC_SUBJECT_CODES = ("ASSEMBLY", "RECESS", "DISMISSAL")

ELEMENT_MULTIPLE_CHOICE = "multiple_choice"
ELEMENT_FILL_BLANK = "fill_blank"
ELEMENT_MATCHING = "matching"
ELEMENT_LABEL_DIAGRAM = "label_diagram"
ELEMENT_DRAWING_AREA = "drawing_area"
ELEMENT_HANDWRITING_AREA = "handwriting_area"
ELEMENT_IMAGE_UPLOAD = "image_upload"
ELEMENT_TEXT_HIGHLIGHT = "text_highlight"
WORKSHEET_ELEMENT_TYPES = (
    ELEMENT_MULTIPLE_CHOICE,
    ELEMENT_FILL_BLANK,
    ELEMENT_MATCHING,
    ELEMENT_LABEL_DIAGRAM,
    ELEMENT_DRAWING_AREA,
    ELEMENT_HANDWRITING_AREA,
    ELEMENT_IMAGE_UPLOAD,
    ELEMENT_TEXT_HIGHLIGHT,
)
CANVAS_ELEMENT_TYPES = (
    ELEMENT_DRAWING_AREA,
    ELEMENT_HANDWRITING_AREA,
    ELEMENT_FILL_BLANK,
    ELEMENT_LABEL_DIAGRAM,
)

CANVAS_OWNER_STUDENT_ANSWER = "student_answer"
CANVAS_OWNER_ANNOTATION = "annotation"
CANVAS_OWNER_GROUP_SHARED = "group_shared"
CANVAS_OWNER_STORYBOOK_ACTIVITY = "storybook_activity"
CANVAS_OWNER_MODEL_ANSWER = "model_answer"
CANVAS_OWNER_TEXTBOOK_PAGE = "textbook_page"

CANVAS_LAYER_BASE = "base"
CANVAS_LAYER_ANNOTATION = "annotation"

CANVAS_TOOLS = ("pen", "highlighter", "eraser", "line", "rectangle", "circle", "arrow")

ASSIGNMENT_TYPE_WORKSHEET = "worksheet"
ASSIGNMENT_TYPE_FILE_UPLOAD = "file_upload"
ASSIGNMENT_TYPE_MIXED = "mixed"
ASSIGNMENT_TYPES = (ASSIGNMENT_TYPE_WORKSHEET, ASSIGNMENT_TYPE_FILE_UPLOAD, ASSIGNMENT_TYPE_MIXED)

DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_CHALLENGING = "challenging"
DIFFICULTIES = (DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_CHALLENGING)

AI_MODE_DISABLED = "disabled"
AI_MODE_HINTS_ONLY = "hints_only"
AI_MODES = (AI_MODE_DISABLED, AI_MODE_HINTS_ONLY)

SUBMISSION_NOT_STARTED = "not_started"
SUBMISSION_IN_PROGRESS = "in_progress"
SUBMISSION_SUBMITTED = "submitted"
SUBMISSION_GRADED = "graded"
SUBMISSION_RETURNED = "returned"
SUBMISSION_NEEDS_REVISION = "needs_revision"
SUBMISSION_STATUSES = (
    SUBMISSION_NOT_STARTED,
    SUBMISSION_IN_PROGRESS,
    SUBMISSION_SUBMITTED,
    SUBMISSION_GRADED,
    SUBMISSION_RETURNED,
    SUBMISSION_NEEDS_REVISION,
)

STORYBOOK_ENGLISH = "english"
STORYBOOK_CHINESE = "chinese"
STORYBOOK_LANGUAGES = (STORYBOOK_ENGLISH, STORYBOOK_CHINESE)

RESOURCE_TYPES = (
    "notes",
    "slides",
    "video",
    "worksheet",
    "homework",
    "storybook",
    "past_paper",
    "practice_paper",
)

ANNOUNCEMENT_TYPES = ("general", "homework_reminder", "test_notification", "school_event")

CALENDAR_EVENT_TYPES = ("school_event", "holiday", "exam", "deadline", "other")
CALENDAR_EVENT_COLORS = {
    "school_event": "violet",
    "holiday": "teal",
    "exam": "coral",
    "deadline": "amber",
    "other": "sky",
}

NOTIFICATION_TYPES = (
    "new_assignment",
    "deadline_reminder",
    "announcement",
    "feedback_received",
    "upcoming_exam",
    "submission_received",
    "overdue_assignment",
    "exam_completed",
    "new_message",
    "new_textbook",
    "revision_requested",
)
