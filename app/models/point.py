from datetime import datetime
from app.extensions import db

class Point(db.Model):
    __tablename__ = "points"
    id_point = db.Column(db.Integer, primary_key=True)
    id_neighborhood = db.Column(db.Integer, db.ForeignKey("neighborhoods.id_neighborhood"), nullable=True)
    id_annotation = db.Column(db.Integer, db.ForeignKey("annotations.id_annotation"), nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    order = db.Column(db.Integer, nullable=True)
    point_type = db.Column(db.String(40), nullable=False)
    __table_args__ = (db.CheckConstraint("(id_neighborhood IS NOT NULL AND id_annotation IS NULL) OR (id_neighborhood IS NULL AND id_annotation IS NOT NULL)", name="ck_point_xor_owner"),)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}