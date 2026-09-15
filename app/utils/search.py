from sqlalchemy import false


_RESERVED_QUERY_KEYS = {"page", "pageSize", "q"}


def _cast_filter_value(field, raw_value):
    try:
        python_type = field.type.python_type
    except Exception:
        return raw_value

    if python_type is bool:
        return str(raw_value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}
    if python_type is int:
        return int(raw_value)
    if python_type is float:
        return float(raw_value)
    return str(raw_value)


def apply_search_filters(query, model, args):
    filters = []
    for key in args.keys():
        if key in _RESERVED_QUERY_KEYS:
            continue
        value = args.get(key)
        if value is None or str(value).strip() == "":
            continue
        filters.append((key, value))

    for key, value in filters:
        field = getattr(model, key, None)
        if field is None:
            continue
        try:
            cast_value = _cast_filter_value(field, value)
        except (TypeError, ValueError):
            return query.filter(false())
        query = query.filter(field == cast_value)

    q_value = (args.get("q") or "").strip()
    if q_value:
        name_field = getattr(model, "name", None)
        if name_field is not None and hasattr(name_field, "ilike"):
            # Usar ilike para insensibilidad a mayúsculas/minúsculas
            query = query.filter(name_field.ilike(f"%{q_value}%"))

    return query
