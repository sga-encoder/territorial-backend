from datetime import datetime
from app.extensions import db

class Annotation(db.Model):
    __tablename__ = "annotations"
    id_annotation = db.Column(db.Integer, primary_key=True)
    id_neighborhood = db.Column(db.Integer, db.ForeignKey("neighborhoods.id_neighborhood"), nullable=True)
    id_citizen = db.Column(db.Integer, db.ForeignKey("citizens.id_citizen"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}