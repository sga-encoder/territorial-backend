from datetime import datetime
from app.extensions import db

class InterestedParty(db.Model):
    __tablename__ = "interested_parties"
    id_interested_party = db.Column(db.Integer, primary_key=True)
    id_entity = db.Column(db.Integer, db.ForeignKey("entities.id_entity"), nullable=False)
    id_annotation = db.Column(db.Integer, db.ForeignKey("annotations.id_annotation"), nullable=False)
    association_date = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("id_entity", "id_annotation", name="uq_interested_entity_annotation"),)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}