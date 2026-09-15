import requests
from flask import Blueprint, jsonify, request

from app.services.report_service import ReportService


bp = Blueprint("report", __name__)
service = ReportService()


@bp.post("/reports")
def create_report():
    data = request.get_json(silent=True) or {}
    query = data.get("query")

    try:
        payload = service.generate(query)
        return jsonify(payload)
    except ValueError as ex:
        return jsonify({"message": str(ex)}), 400
    except requests.RequestException as ex:
        return jsonify({"message": f"Error calling Gemini: {str(ex)}"}), 502
    except Exception as ex:
        return jsonify({"message": f"Unexpected error: {str(ex)}"}), 500


@bp.get("/reports/test/pie")
def test_pie_report():
    return jsonify(
        {
            "type": "pie",
            "labels": ["Team A", "Team B", "Team C", "Team D", "Team E"],
            "series": [44, 55, 13, 43, 22],
        }
    )


@bp.get("/reports/test/bar")
def test_bar_report():
    return jsonify(
        {
            "type": "bar",
            "labels": [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
                "Bonus",
            ],
            "series": [
                {
                    "name": "Servings",
                    "data": [44, 55, 41, 67, 22, 43, 21, 33, 45, 31, 87, 65, 35],
                }
            ],
        }
    )


@bp.get("/reports/test/line")
def test_line_report():
    return jsonify(
        {
            "type": "line",
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "series": [
                {"name": "High - 2013", "data": [28, 29, 33, 36, 32, 32, 33]},
                {"name": "Low - 2013", "data": [12, 11, 14, 18, 17, 13, 13]},
            ],
        }
    )