from datetime import datetime
from app.extensions import db

class Vote(db.Model):
    __tablename__ = "votes"
    id_vote = db.Column(db.Integer, primary_key=True)
    id_citizen = db.Column(db.Integer, db.ForeignKey("citizens.id_citizen"), nullable=False)
    id_annotation = db.Column(db.Integer, db.ForeignKey("annotations.id_annotation"), nullable=False)
    stars = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    vote_date = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("id_citizen", "id_annotation", name="uq_vote_citizen_annotation"), db.CheckConstraint("stars BETWEEN 1 AND 5", name="ck_vote_stars_range"),)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}