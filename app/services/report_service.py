import os
import re
from pathlib import Path
from typing import Dict, List, Literal

import requests
from pydantic import BaseModel, ValidationError
from sqlalchemy import text

from app.extensions import db


class GeminiReportOutput(BaseModel):
    sql: str
    type: Literal["pie", "bar", "line", "series"]


class ReportService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        raw_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
        self.model = self._normalize_model_name(raw_model)
        self.models_context = self._load_models_context()

    def generate(self, query: str):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("'query' is required and must be a non-empty string")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing in environment")

        gemini_output = self._ask_gemini(query.strip())
        safe_sql = self._sanitize_sql(gemini_output.sql)
        rows = self._execute_sql(safe_sql)
        return self._build_chart_response(gemini_output.type, rows)

    def _ask_gemini(self, user_query: str) -> GeminiReportOutput:
        prompt = (
            "genera una consulta sql para resolver la query del usuario, ten en cuenta que la estructura de la base de datos está en models_toon.txt. "
            "La base usa tablas en plural (ejemplo: communes, neighborhoods, annotations). "
            "Devuelve SOLO JSON con este formato exacto: "
            '{"sql":"SELECT ...","type":"pie|bar|line|series"}. '
            f"Query del usuario: {user_query}. "
            f"Estructura de referencia:\n{self.models_context}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0,
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "sql": {"type": "STRING"},
                        "type": {"type": "STRING", "enum": ["pie", "bar", "line", "series"]},
                    },
                    "required": ["sql", "type"],
                },
            },
        }

        response = self._call_generate_content(self.model, payload)
        if response.status_code == 404:
            discovered_model = self._discover_generate_content_model()
            if discovered_model and discovered_model != self.model:
                self.model = discovered_model
                response = self._call_generate_content(self.model, payload)

        if response.status_code >= 400:
            raise ValueError(self._build_gemini_http_error(response))

        raw_text = self._extract_text_from_gemini(response.json())

        try:
            return GeminiReportOutput.model_validate_json(self._strip_markdown_fences(raw_text))
        except ValidationError as ex:
            raise ValueError(f"Invalid Gemini response format: {str(ex)}") from ex

    def _load_models_context(self) -> str:
        models_file = Path(__file__).resolve().parent.parent / "models" / "models_toon.txt"
        if not models_file.exists():
            return "models_toon.txt not found"
        return models_file.read_text(encoding="utf-8")

    def _extract_text_from_gemini(self, data: Dict) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            raise ValueError("Gemini returned no candidates")

        content = candidates[0].get("content") or {}
        parts = content.get("parts") or []
        for part in parts:
            if isinstance(part, dict) and part.get("text"):
                return part["text"]

        raise ValueError("Gemini response has no text part")

    def _build_gemini_http_error(self, response: requests.Response) -> str:
        try:
            body = response.json()
            error = body.get("error") or {}
            message = error.get("message") or response.text
            status = error.get("status") or str(response.status_code)
            return f"Gemini HTTP {response.status_code} ({status}): {message}"
        except Exception:
            return f"Gemini HTTP {response.status_code}: {response.text}"

    def _call_generate_content(self, model_name: str, payload: Dict) -> requests.Response:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        return requests.post(url, json=payload, timeout=30)

    def _discover_generate_content_model(self) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        response = requests.get(url, timeout=30)
        if response.status_code >= 400:
            return self.model

        data = response.json() if response.content else {}
        models = data.get("models") or []
        supported = []

        for model_info in models:
            methods = model_info.get("supportedGenerationMethods") or []
            if "generateContent" not in methods:
                continue

            name = str(model_info.get("name", ""))
            if not name.startswith("models/"):
                continue
            supported.append(name.replace("models/", "", 1))

        if not supported:
            return self.model

        preferred_order = [
            "gemini-1.5-flash"
        ]

        for preferred in preferred_order:
            if preferred in supported:
                return preferred

        return supported[0]

    def _normalize_model_name(self, model_name: str) -> str:
        aliases = {
            "gemini-1.5": "gemini-1.5-flash",
        }
        normalized = aliases.get(model_name, model_name)
        return normalized or "gemini-1.5-flash"

    def _strip_markdown_fences(self, text_value: str) -> str:
        cleaned = text_value.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        return cleaned

    def _sanitize_sql(self, sql_query: str) -> str:
        sql = sql_query.strip().rstrip(";").strip()
        sql_lower = sql.lower()

        if ";" in sql:
            raise ValueError("Only one SQL statement is allowed")

        if not (sql_lower.startswith("select") or sql_lower.startswith("with")):
            raise ValueError("Only SELECT queries are allowed")

        blocked_tokens = [
            " insert ",
            " update ",
            " delete ",
            " drop ",
            " alter ",
            " create ",
            " truncate ",
            " replace ",
            " attach ",
            " detach ",
            " pragma ",
            " vacuum ",
        ]

        padded_sql = f" {sql_lower} "
        if any(token in padded_sql for token in blocked_tokens):
            raise ValueError("Unsafe SQL detected")

        return sql

    def _execute_sql(self, sql_query: str) -> List[Dict]:
        print(f"Executing SQL: {sql_query}")
        result = db.session.execute(text(sql_query))
        return [dict(row) for row in result.mappings().all()]

    def _build_chart_response(self, chart_type: str, rows: List[Dict]):
        if chart_type == "series":
            chart_type = "line"

        if chart_type == "pie":
            return self._build_pie(rows)
        if chart_type == "bar":
            return self._build_bar(rows)
        return self._build_line(rows)

    def _build_pie(self, rows: List[Dict]):
        if not rows:
            return {"type": "pie", "labels": [], "series": []}

        columns = list(rows[0].keys())
        label_col = columns[0]
        value_col = self._first_numeric_column(columns[1:], rows) or (columns[1] if len(columns) > 1 else columns[0])

        labels = [str(row.get(label_col, "")) for row in rows]
        series = [self._to_number(row.get(value_col)) for row in rows]
        return {"type": "pie", "labels": labels, "series": series}

    def _build_bar(self, rows: List[Dict]):
        if not rows:
            return {"type": "bar", "series": []}

        columns = list(rows[0].keys())
        labels_col = columns[0]
        value_cols = [col for col in columns[1:] if self._is_numeric_column(col, rows)]
        if not value_cols:
            value_cols = columns[1:2] if len(columns) > 1 else columns[:1]

        series = []
        for col in value_cols:
            series.append(
                {
                    "name": col,
                    "data": [self._to_number(row.get(col)) for row in rows],
                }
            )

        return {
            "type": "bar",
            "labels": [str(row.get(labels_col, "")) for row in rows],
            "series": series,
        }

    def _build_line(self, rows: List[Dict]):
        if not rows:
            return {"type": "line", "series": []}

        columns = list(rows[0].keys())
        if len(columns) >= 3:
            x_col, name_col, value_col = columns[0], columns[1], columns[2]
            labels = []
            seen_labels = set()
            grouped = {}

            for row in rows:
                x_value = str(row.get(x_col, ""))
                if x_value not in seen_labels:
                    labels.append(x_value)
                    seen_labels.add(x_value)

                series_name = str(row.get(name_col, "Series"))
                grouped.setdefault(series_name, []).append(self._to_number(row.get(value_col)))

            series = [{"name": name, "data": data} for name, data in grouped.items()]
            return {"type": "line", "labels": labels, "series": series}

        x_col = columns[0]
        y_col = self._first_numeric_column(columns[1:], rows) or (columns[1] if len(columns) > 1 else columns[0])
        return {
            "type": "line",
            "labels": [str(row.get(x_col, "")) for row in rows],
            "series": [{"name": y_col, "data": [self._to_number(row.get(y_col)) for row in rows]}],
        }

    def _first_numeric_column(self, columns: List[str], rows: List[Dict]):
        for column in columns:
            if self._is_numeric_column(column, rows):
                return column
        return None

    def _is_numeric_column(self, column: str, rows: List[Dict]) -> bool:
        for row in rows:
            value = row.get(column)
            if value is None:
                continue
            if isinstance(value, (int, float)):
                return True
        return False

    def _to_number(self, value):
        if value is None:
            return 0
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return value

        string_value = str(value).strip()
        if not string_value:
            return 0

        try:
            number = float(string_value)
            return int(number) if number.is_integer() else number
        except (TypeError, ValueError):
            return 0