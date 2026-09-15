from app.repositories.point_repository import PointRepository

class PointService:
    def __init__(self):
        self.repository = PointRepository()

    def list(self):
        return self.repository.list()

    def get_or_fail(self, item_id):
        item = self.repository.get(item_id)
        if item is None:
            raise ValueError("Record not found")
        return item

    def search(self, value):
        return self.repository.search(value)

    def create(self, data):
        has_neighborhood = data.get("id_neighborhood") not in (None, "")
        has_annotation = data.get("id_annotation") not in (None, "")

        if has_neighborhood and has_annotation:
            raise ValueError("Solo se puede enviar uno de los dos campos: id_neighborhood o id_annotation")
        if not has_neighborhood and not has_annotation:
            raise ValueError("Debes enviar uno de los dos campos: id_neighborhood o id_annotation")

        return self.repository.create(data)

    def update(self, item_id, data):
        item = self.get_or_fail(item_id)
        return self.repository.update(item, data)

    def delete(self, item_id):
        item = self.get_or_fail(item_id)
        self.repository.delete(item)
