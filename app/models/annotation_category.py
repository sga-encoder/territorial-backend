from datetime import datetime
from app.extensions import db

class AnnotationCategory(db.Model):
    __tablename__ = "annotation_categories"
    id_annotation_category = db.Column(db.Integer, primary_key=True)
    id_category = db.Column(db.Integer, db.ForeignKey("categories.id_category"), nullable=False)
    id_annotation = db.Column(db.Integer, db.ForeignKey("annotations.id_annotation"), nullable=False)
    __table_args__ = (db.UniqueConstraint("id_category", "id_annotation", name="uq_category_annotation"),)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}