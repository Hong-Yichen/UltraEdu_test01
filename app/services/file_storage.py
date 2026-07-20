import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename


def save_upload(file_storage, subject_code):
    """Save an uploaded file under UPLOAD_FOLDER/<subject_code>/ with a collision-proof name.

    Returns the path relative to UPLOAD_FOLDER (forward-slash separated), suitable for
    storing in the DB and for building download URLs.
    """
    filename = secure_filename(file_storage.filename or "file")
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    subject_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], subject_code)
    os.makedirs(subject_dir, exist_ok=True)
    dest_path = os.path.join(subject_dir, unique_name)
    file_storage.save(dest_path)
    return f"{subject_code}/{unique_name}"


def absolute_upload_path(relative_path):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], relative_path)
