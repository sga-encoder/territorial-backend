from app.repositories.city_repository import CityRepository
class CityService:
    def __init__(self): self.repository = CityRepository()
    def list(self): return self.repository.list()
    def get_or_fail(self, item_id):
        item = self.repository.get(item_id)
        if item is None: raise ValueError("Record not found")
        return item
    def search(self, value): return self.repository.search(value)
    def create(self, data): return self.repository.create(data)
    def update(self, item_id, data): return self.repository.update(self.get_or_fail(item_id), data)
    def delete(self, item_id): self.repository.delete(self.get_or_fail(item_id))
