import sys
import json
from urllib.request import Request, urlopen
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.extensions import db
from app.models.department import Department
from app.models.city import City
from app.models.commune import Commune
from app.models.neighborhood import Neighborhood
from app.models.citizen import Citizen
from app.models.entity import Entity
from app.models.official import Official
from app.models.category import Category
from app.models.annotation import Annotation
from app.models.point import Point
from app.models.annotation_category import AnnotationCategory
from app.models.interested_party import InterestedParty
from app.models.vote import Vote
from app.models.evidence import Evidence

API_COLOMBIA_BASE_URL = "https://api-colombia.com/api/v1"


def fetch_json(url):
    req = Request(url, headers={"User-Agent": "territorial-backend-seed/1.0"})
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def seed_departments_and_cities():
    departments_data = fetch_json(f"{API_COLOMBIA_BASE_URL}/Department")
    cities_data = fetch_json(f"{API_COLOMBIA_BASE_URL}/City")

    departments_by_api_id = {}
    departments_to_add = []
    for department_data in departments_data:
        department = Department(
            name=department_data["name"].strip(),
            dane_code=f"{int(department_data['id']):02d}",
        )
        departments_by_api_id[department_data["id"]] = department
        departments_to_add.append(department)

    db.session.add_all(departments_to_add)
    db.session.flush()

    # Evita duplicados que violen uq_city_department_name.
    seen_cities = set()
    cities_to_add = []
    for city_data in cities_data:
        department = departments_by_api_id.get(city_data.get("departmentId"))
        city_name = (city_data.get("name") or "").strip()
        if not department or not city_name:
            continue

        dedupe_key = (department.id_department, city_name.casefold())
        if dedupe_key in seen_cities:
            continue

        seen_cities.add(dedupe_key)
        cities_to_add.append(
            City(
                id_department=department.id_department,
                name=city_name,
                dane_code=f"{int(city_data['id']):05d}",
            )
        )

    db.session.add_all(cities_to_add)
    db.session.flush()

    return departments_to_add, cities_to_add


app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    departments, cities = seed_departments_and_cities()

    manizales = next((city for city in cities if city.name == "Manizales"), None)
    if manizales is None:
        raise RuntimeError("No se encontro Manizales en API Colombia para continuar el seed base.")

    commune = Commune(id_city=manizales.id_city, name="Comuna 8 - Bosques del Norte", status="active")
    db.session.add(commune)
    db.session.flush()

    neighborhood = Neighborhood(id_commune=commune.id_commune, name="Bosques del Norte", status="active")
    citizen = Citizen(name="Carolina Martinez", email="carolina@example.com", phone="3001234567", address="Cra 23 # 62-15", latitude=5.095742, longitude=-75.514832, status="active")
    entity = Entity(name="Alcaldia de Manizales", nit="890.801.053-3", phone="(606) 892 80 00", email="contacto@manizales.gov.co", address="Carrera 21 # 19-22", logo_url="logos/alcaldia.png", status="active")
    db.session.add_all([neighborhood, citizen, entity])
    db.session.flush()

    official = Official(id_entity=entity.id_entity, name="Laura Gomez", email="laura.gomez@manizales.gov.co", phone="3112345678", role="official", status="active", last_latitude=5.096, last_longitude=-75.515, gps_active=True)
    cat = Category(name="Infrastructure", description="Issues related to infrastructure", image_url="categories/infrastructure.png", status="active")
    db.session.add_all([official, cat])
    db.session.flush()

    subcat = Category(id_parent_category=cat.id_category, name="Roads and sidewalks", description="Road damage", status="active")
    annotation = Annotation(id_neighborhood=neighborhood.id_neighborhood, id_citizen=citizen.id_citizen, description="Large pothole on the road", latitude=5.095742, longitude=-75.514832, status="open")
    db.session.add_all([subcat, annotation])
    db.session.flush()

    db.session.add_all([
        Point(id_neighborhood=neighborhood.id_neighborhood, latitude=5.095742, longitude=-75.514832, order=1, point_type="boundary"),
        Point(id_annotation=annotation.id_annotation, latitude=5.095742, longitude=-75.514832, order=1, point_type="annotation"),
        AnnotationCategory(id_category=cat.id_category, id_annotation=annotation.id_annotation),
        InterestedParty(id_entity=entity.id_entity, id_annotation=annotation.id_annotation),
        Vote(id_citizen=citizen.id_citizen, id_annotation=annotation.id_annotation, stars=4, comment="Very important to fix."),
        Evidence(id_annotation=annotation.id_annotation, file_url="evidences/pothole.jpg", file_type="image/jpeg", file_size=1024),
    ])
    db.session.commit()
    print(f"Database seeded successfully. Departments: {len(departments)}, Cities: {len(cities)}")
