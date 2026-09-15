from flask import Blueprint, request, jsonify
from app.services.city_service import CityService
from app.utils.pagination import apply_pagination
from app.utils.search import apply_search_filters
bp = Blueprint("city", __name__, url_prefix="/api/cities")
service = CityService()
@bp.get("")
def list_items(): return jsonify(apply_pagination(service.list(), service.repository.model, request.args.get("page"), request.args.get("pageSize")))
@bp.get("/<int:item_id>")
def get_item(item_id):
    try: return jsonify(service.get_or_fail(item_id).to_dict())
    except ValueError as ex: return jsonify({"message": str(ex)}), 404
@bp.get("/search")
def search_items(): return jsonify(apply_pagination(apply_search_filters(service.list(), service.repository.model, request.args), service.repository.model, request.args.get("page"), request.args.get("pageSize")))
@bp.post("")
def create_item():
    try: return jsonify(service.create(request.get_json() or {}).to_dict()), 201
    except Exception as ex: return jsonify({"message": str(ex)}), 400
@bp.put("/<int:item_id>")
def update_item(item_id):
    try: return jsonify(service.update(item_id, request.get_json() or {}).to_dict())
    except ValueError as ex: return jsonify({"message": str(ex)}), 404
    except Exception as ex: return jsonify({"message": str(ex)}), 400
@bp.delete("/<int:item_id>")
def delete_item(item_id):
    try: service.delete(item_id); return jsonify({"message": "Record deleted successfully"})
    except ValueError as ex: return jsonify({"message": str(ex)}), 404
    except Exception as ex: return jsonify({"message": str(ex)}), 400
