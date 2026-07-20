"""Stubbed AI hint seam.

This is the single place a real model call (e.g. the Anthropic API) would slot in later.
For now it returns a canned, type-aware hint — never an answer — so the AI toggle, UI hook,
and endpoint can be fully wired and tested without a live API key.
"""

_GENERIC_HINTS_BY_TYPE = {
    "multiple_choice": "Try ruling out the options that clearly don't fit, then compare what's left against the question.",
    "fill_blank": "Reread the sentence around the blank — what value would make both sides of the relationship match?",
    "matching": "Look for the strongest, most obvious pair first, then work outward from there.",
    "label_diagram": "Identify any labels you're confident about first, then use those as anchors for the rest.",
    "drawing_area": "Sketch the simplest version of the shape or diagram first, then add detail.",
    "handwriting_area": "Write out your steps one at a time — it's easier to spot where to go next once they're on paper.",
    "image_upload": "Make sure your uploaded work clearly shows each step, not just the final result.",
    "text_highlight": "Reread the passage once fully before highlighting, so you catch the most relevant sentences.",
}

_DEFAULT_HINT = "Break the problem into smaller steps, and check each one before moving to the next."


def get_hint(worksheet_element):
    """Return a canned hint string for the given WorksheetElement. Never returns an answer."""
    return _GENERIC_HINTS_BY_TYPE.get(worksheet_element.element_type, _DEFAULT_HINT)
