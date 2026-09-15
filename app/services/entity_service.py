from app.repositories.entity_repository import EntityRepository

class EntityService:
    def __init__(self):
        self.repository = EntityRepository()

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
        self._validate_unique_fields(data)
        return self.repository.create(data)

    def update(self, item_id, data):
        item = self.get_or_fail(item_id)
        self._validate_unique_fields(data, current_id=item.id_entity)
        return self.repository.update(item, data)

    def delete(self, item_id):
        item = self.get_or_fail(item_id)
        self.repository.delete(item)

    def _validate_unique_fields(self, data, current_id=None):
        model = self.repository.model

        email = (data.get("email") or "").strip()
        if email:
            existing = model.query.filter(model.email == email).first()
            if existing and existing.id_entity != current_id:
                raise ValueError("El email ya está registrado")

        name = (data.get("name") or "").strip()
        if name:
            existing = model.query.filter(model.name == name).first()
            if existing and existing.id_entity != current_id:
                raise ValueError("El nombre de la entidad ya está registrado")
