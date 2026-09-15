from datetime import datetime
from app.extensions import db

class Evidence(db.Model):
    __tablename__ = "evidences"
    id_evidence = db.Column(db.Integer, primary_key=True)
    id_annotation = db.Column(db.Integer, db.ForeignKey("annotations.id_annotation"), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(60), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}