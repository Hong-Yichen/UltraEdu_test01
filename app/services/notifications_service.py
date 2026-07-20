from app.extensions import db
from app.models.notification import Notification


def create_notification(user_id, type_, title, body=None, link_url=None,
                         related_object_type=None, related_object_id=None):
    notification = Notification(
        user_id=user_id,
        type=type_,
        title=title,
        body=body,
        link_url=link_url,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
    )
    db.session.add(notification)
    return notification


def notify_class(student_ids, type_, title, body=None, link_url=None,
                  related_object_type=None, related_object_id=None):
    for student_id in student_ids:
        create_notification(
            student_id, type_, title, body, link_url, related_object_type, related_object_id
        )
