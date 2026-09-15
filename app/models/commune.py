from datetime import datetime
from app.extensions import db

class Commune(db.Model):
    __tablename__ = "communes"
    id_commune = db.Column(db.Integer, primary_key=True)
    id_city = db.Column(db.Integer, db.ForeignKey("cities.id_city"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("id_city", "name", name="uq_commune_city_name"),)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}