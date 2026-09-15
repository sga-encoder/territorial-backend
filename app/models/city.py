from datetime import datetime
from app.extensions import db

class City(db.Model):
    __tablename__ = "cities"
    id_city = db.Column(db.Integer, primary_key=True)
    id_department = db.Column(db.Integer, db.ForeignKey("departments.id_department"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    dane_code = db.Column(db.String(20), nullable=True, unique=True)
    communes = db.relationship("Commune", backref="city", lazy=True)
    __table_args__ = (db.UniqueConstraint("id_department", "name", name="uq_city_department_name"),)

    def to_dict(self):
        return {"id_city": self.id_city, "id_department": self.id_department, "name": self.name, "dane_code": self.dane_code}
