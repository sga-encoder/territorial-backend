import os
from uuid import uuid4

import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
CLOUDINARY_ROOT_FOLDER = "territorial"


def cloudinary_enabled():
    # The SDK reads CLOUDINARY_URL (cloudinary://key:secret@cloud) from the environment.
    return bool(os.getenv("CLOUDINARY_URL")) and bool(cloudinary.config().cloud_name)


def upload_to_cloudinary(source, folder_name, public_id=None, image_format=None):
    """Uploads a file-like object, path or bytes and returns Cloudinary's upload response."""
    options = {"folder": f"{CLOUDINARY_ROOT_FOLDER}/{folder_name}", "resource_type": "image"}
    if public_id:
        options.update(public_id=public_id, overwrite=True, invalidate=True)
    if image_format:
        options["format"] = image_format
    return cloudinary.uploader.upload(source, **options)


def save_uploaded_file(file, folder_name):
    if not file or file.filename == "":
        return None
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Invalid file extension. Allowed: png, jpg, jpeg, webp")
    if cloudinary_enabled():
        return upload_to_cloudinary(file.stream, folder_name)["secure_url"]
    filename = secure_filename(f"{uuid4().hex}.{ext}")
    base = current_app.config["UPLOAD_FOLDER"]
    folder = os.path.join(base, folder_name)
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return f"/api/images/{folder_name}/{filename}"
