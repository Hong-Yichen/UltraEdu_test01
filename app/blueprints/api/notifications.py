from flask import jsonify, request
from flask_login import login_required, current_user

from app.blueprints.api import api_bp
from app.extensions import db
from app.models.notification import Notification


def _serialize(n):
    return {
        "id": n.id,
        "type": n.type,
        "title": n.title,
        "body": n.body,
        "link_url": n.link_url,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat(),
    }


@api_bp.route("/notifications")
@login_required
def list_notifications():
    query = Notification.query.filter_by(user_id=current_user.id)
    if request.args.get("unread_only") == "true":
        query = query.filter_by(is_read=False)
    since = request.args.get("since")
    if since:
        query = query.filter(Notification.created_at > since)
    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify(
        {
            "notifications": [_serialize(n) for n in notifications],
            "unread_count": unread_count,
        }
    )


@api_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first_or_404()
    notification.is_read = True
    db.session.commit()
    return jsonify({"status": "ok"})


@api_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"status": "ok"})
