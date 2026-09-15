import os
from uuid import uuid4
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def save_uploaded_file(file, folder_name):
    if not file or file.filename == "":
        return None
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Invalid file extension. Allowed: png, jpg, jpeg, webp")
    filename = secure_filename(f"{uuid4().hex}.{ext}")
    base = current_app.config["UPLOAD_FOLDER"]
    folder = os.path.join(base, folder_name)
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return f"/api/images/{folder_name}/{filename}"
