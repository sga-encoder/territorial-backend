from datetime import datetime
from app.extensions import db

class Entity(db.Model):
    __tablename__ = "entities"
    id_entity = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, unique=True)
    nit = db.Column(db.String(40), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    email = db.Column(db.String(160), nullable=True, unique=True)
    address = db.Column(db.String(255), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), nullable=False)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}