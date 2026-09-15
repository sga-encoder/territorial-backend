from app.extensions import db
from app.models.vote import Vote

class VoteRepository:
    model = Vote

    def list(self):
        return self.model.query

    def get(self, item_id):
        return self.model.query.get(item_id)

    def search(self, value):
        field = getattr(self.model, "id_vote")
        return self.model.query.filter(field.ilike(f"%{value}%")) if hasattr(field, "ilike") else self.model.query.filter(field == value)

    def create(self, data):
        item = self.model(**data)
        db.session.add(item)
        db.session.commit()
        return item

    def update(self, item, data):
        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        db.session.commit()
        return item

    def delete(self, item):
        db.session.delete(item)
        db.session.commit()
