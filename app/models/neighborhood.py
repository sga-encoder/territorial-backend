from datetime import datetime
from app.extensions import db

class Neighborhood(db.Model):
    __tablename__ = "neighborhoods"
    id_neighborhood = db.Column(db.Integer, primary_key=True)
    id_commune = db.Column(db.Integer, db.ForeignKey("communes.id_commune"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("id_commune", "name", name="uq_neighborhood_commune_name"),)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}