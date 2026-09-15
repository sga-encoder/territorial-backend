import os
from flask import Blueprint, send_from_directory, current_app, abort

bp = Blueprint("images", __name__, url_prefix="/api/images")

@bp.get("/<path:relative_path>")
def get_image(relative_path):
    base = current_app.config["UPLOAD_FOLDER"]
    full_path = os.path.abspath(os.path.join(base, relative_path))
    base_path = os.path.abspath(base)
    if not full_path.startswith(base_path) or not os.path.exists(full_path):
        abort(404)
    directory, filename = os.path.split(full_path)
    return send_from_directory(directory, filename)
