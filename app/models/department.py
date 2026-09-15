from datetime import datetime
from app.extensions import db

class Department(db.Model):
    __tablename__ = "departments"
    id_department = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    dane_code = db.Column(db.String(20), nullable=True, unique=True)
    cities = db.relationship("City", backref="department", lazy=True)

    def to_dict(self):
        return {"id_department": self.id_department, "name": self.name, "dane_code": self.dane_code}
