from flask import Blueprint, request, jsonify, current_app
from app.services.official_service import OfficialService
from app.services.official_tracking_service import OfficialTrackingService
from app.utils.pagination import apply_pagination
from app.utils.search import apply_search_filters
from app.utils.files import save_uploaded_file

bp = Blueprint("official", __name__, url_prefix="/api/officials")
service = OfficialService()
tracking_service = OfficialTrackingService()

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
        item = service.create(data)
        return jsonify(item.to_dict()), 201
    except Exception as ex:
        return jsonify({"message": str(ex)}), 400

@bp.put("/<int:item_id>")
def update_item(item_id):
    try:
        data = request.form.to_dict() if request.content_type and "multipart/form-data" in request.content_type else (request.get_json() or {})
        item = service.update(item_id, data)
        return jsonify(item.to_dict())
    except ValueError as ex:
        return jsonify({"message": str(ex)}), 404
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


@bp.post("/tracking/start")
def start_tracking():
    data = request.get_json() or {}
    official_ids = data.get("ids")
    if not isinstance(official_ids, list) or not official_ids:
        return jsonify({"message": "ids must be a non-empty list"}), 400

    app = current_app._get_current_object()
    result = tracking_service.start_tracking(official_ids, app)
    return jsonify(result)


@bp.post("/tracking/stop")
def stop_tracking():
    data = request.get_json() or {}
    official_ids = data.get("ids")
    if official_ids is not None and not isinstance(official_ids, list):
        return jsonify({"message": "ids must be a list when provided"}), 400

    result = tracking_service.stop_tracking(official_ids)
    return jsonify(result)
