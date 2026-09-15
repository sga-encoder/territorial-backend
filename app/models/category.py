from datetime import datetime
from app.extensions import db

class Category(db.Model):
    __tablename__ = "categories"
    id_category = db.Column(db.Integer, primary_key=True)
    id_parent_category = db.Column(db.Integer, db.ForeignKey("categories.id_category"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), nullable=False)
    __table_args__ = (db.UniqueConstraint("id_parent_category", "name", name="uq_category_parent_name"),)

    def to_dict(self):
        return {c.name: (getattr(self, c.name).isoformat() if hasattr(getattr(self, c.name), "isoformat") and getattr(self, c.name) is not None else getattr(self, c.name)) for c in self.__table__.columns}