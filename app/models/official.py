from datetime import datetime
from app.extensions import db

class Official(db.Model):
    __tablename__ = "officials"
    id_official = db.Column(db.Integer, primary_key=True)
    id_entity = db.Column(db.Integer, db.ForeignKey("entities.id_entity"), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True)
    phone = db.Column(db.String(40), nullable=True)
    role = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    last_latitude = db.Column(db.Float, nullable=True)
    last_longitude = db.Column(db.Float, nullable=True)
    last_gps_update = db.Column(db.DateTime, nullable=True)
    gps_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}