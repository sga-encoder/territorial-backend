from flask import Blueprint, request, jsonify
from app.services.entity_service import EntityService
from app.utils.pagination import apply_pagination
from app.utils.search import apply_search_filters
from app.utils.files import save_uploaded_file

bp = Blueprint("entity", __name__, url_prefix="/api/entities")
service = EntityService()

@bp.get("")
def list_items():
    query = service.list()
    return jsonify(apply_pagination(query, service.repository.model, request.args.get("page"), request.args.get("pageSize")))

@bp.get("/<int:item_id>")
def get_item(item_id):
    try:
        return jsonify(service.get_or_fail(item_id).to_dict())
    except ValueError as ex:
        return jsonify({"message": str(ex)}), 404

@bp.get("/search")
def search_items():
    query = apply_search_filters(service.list(), service.repository.model, request.args)
    return jsonify(apply_pagination(query, service.repository.model, request.args.get("page"), request.args.get("pageSize")))

@bp.post("")
def create_item():
    try:
        data = request.form.to_dict() if request.content_type and "multipart/form-data" in request.content_type else (request.get_json() or {})
        if "file" in request.files:
            data["logo_url"] = save_uploaded_file(request.files["file"], "logos")
        item = service.create(data)
        return jsonify(item.to_dict()), 201
    except Exception as ex:
        return jsonify({"message": str(ex)}), 400

@bp.put("/<int:item_id>")
def update_item(item_id):
    try:
        data = request.form.to_dict() if request.content_type and "multipart/form-data" in request.content_type else (request.get_json() or {})
        if "file" in request.files:
            data["logo_url"] = save_uploaded_file(request.files["file"], "logos")
        item = service.update(item_id, data)
        return jsonify(item.to_dict())
    except ValueError as ex:
        status = 404 if str(ex) == "Record not found" else 400
        return jsonify({"message": str(ex)}), status
    except Exception as ex:
        return jsonify({"message": str(ex)}), 400

@bp.delete("/<int:item_id>")
def delete_item(item_id):
    try:
        service.delete(item_id)
        return jsonify({"message": "Record deleted successfully"})
    except ValueError as ex:
        return jsonify({"message": str(ex)}), 404
    except Exception as ex:
        return jsonify({"message": str(ex)}), 400
