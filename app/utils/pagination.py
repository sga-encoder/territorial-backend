def apply_pagination(query, model, page, page_size):
    if page is None or page_size is None:
        return [item.to_dict() for item in query.all()]
    page = int(page)
    page_size = int(page_size)
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    return {
        "page": page,
        "pageSize": page_size,
        "totalItems": pagination.total,
        "totalPages": pagination.pages,
        "items": [item.to_dict() for item in pagination.items],
    }
