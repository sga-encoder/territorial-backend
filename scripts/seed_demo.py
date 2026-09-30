"""Demo seed: rebuilds the database with rich, coherent sample data for exhibitions.

WARNING: drops and recreates every table (same as scripts/seed.py).

Usage:
    python scripts/seed_demo.py

Output is deterministic (fixed random seed). Person names are invented and all
e-mails use the reserved example.com domain. Images are generated as SVG files
inside UPLOAD_FOLDER and stored as /api/images/<folder>/<file> (same format as
app/utils/files.py). Firebase login accounts are created separately with
scripts/seed_firebase_users.py.
"""
import json
import math
import random
import sys
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.annotation import Annotation  # noqa: E402
from app.models.annotation_category import AnnotationCategory  # noqa: E402
from app.models.category import Category  # noqa: E402
from app.models.citizen import Citizen  # noqa: E402
from app.models.city import City  # noqa: E402
from app.models.commune import Commune  # noqa: E402
from app.models.department import Department  # noqa: E402
from app.models.entity import Entity  # noqa: E402
from app.models.evidence import Evidence  # noqa: E402
from app.models.interested_party import InterestedParty  # noqa: E402
from app.models.neighborhood import Neighborhood  # noqa: E402
from app.models.official import Official  # noqa: E402
from app.models.point import Point  # noqa: E402
from app.models.vote import Vote  # noqa: E402

RANDOM_SEED = 42
API_COLOMBIA_BASE_URL = "https://api-colombia.com/api/v1"
EMAIL_DOMAIN = "example.com"
# Fixed reference date so the generated timeline is reproducible.
REFERENCE_DATE = datetime(2026, 9, 30, 12, 0, 0)

# Neighborhood polygons are laid out on a grid; the radius stays below half the
# spacing so polygons never overlap.
GRID_SPACING = 0.0075
POLYGON_RADIUS = 0.0031
CENTER_JITTER = 0.0003

OFFLINE_DEPARTMENTS = [
    ("Caldas", "17", [("Manizales", "17001"), ("Villamaría", "17873"), ("Chinchiná", "17174"),
                      ("Neira", "17486"), ("Palestina", "17524"), ("Riosucio", "17614")]),
    ("Risaralda", "66", [("Pereira", "66001"), ("Dosquebradas", "66170"), ("Santa Rosa de Cabal", "66682")]),
    ("Antioquia", "05", [("Medellín", "05001"), ("Envigado", "05266"), ("Rionegro", "05615")]),
    ("Bogotá D.C.", "11", [("Bogotá", "11001")]),
    ("Valle del Cauca", "76", [("Cali", "76001"), ("Palmira", "76520")]),
]

# (city, grid origin lat/lng, grid columns, [(commune, [neighborhoods])])
TERRITORY = [
    ("Manizales", (5.0905, -75.5350), 8, [
        ("Comuna Atardeceres", ["Chipre", "El Carmen", "Villa Pilar", "La Francia"]),
        ("Comuna San José", ["San José", "Galán", "Sierra Morena", "Las Delicias"]),
        ("Comuna Cumanday", ["Centro Histórico", "San Joaquín", "Hoyo Frío", "Liborio"]),
        ("Comuna La Estación", ["Versalles", "Los Alcázares", "Arenales", "La Estación"]),
        ("Comuna Ciudadela del Norte", ["Bosques del Norte", "San Sebastián", "Solferino", "Villa Hermosa"]),
        ("Comuna Ecoturístico Cerro de Oro", ["Cerro de Oro", "Aranjuez", "Morrogacho", "Alta Suiza"]),
        ("Comuna Tesorito", ["Tesorito", "San Marcel", "La Carola", "Baja Suiza"]),
        ("Comuna Palogrande", ["Palogrande", "Laureles", "Palermo", "La Estrella"]),
        ("Comuna Universitaria", ["Fátima", "Lusitania", "La Enea", "Minitas"]),
        ("Comuna La Fuente", ["La Fuente", "Villa Carmenza", "El Nevado", "Buenos Aires"]),
        ("Comuna La Macarena", ["La Macarena", "Bajo Andes", "Colombia", "Villa Julia"]),
    ]),
    ("Villamaría", (5.0385, -75.5230), 6, [
        ("Comuna Centro Villamaría", ["Centro", "El Pradito", "Los Cerezos"]),
        ("Comuna Llanitos", ["Llanitos", "Turín", "La Floresta"]),
    ]),
]

FIRST_NAMES = [
    "Valentina", "Santiago", "Mariana", "Sebastián", "Isabella", "Mateo", "Daniela", "Samuel",
    "Gabriela", "Nicolás", "Sofía", "Alejandro", "Camila", "Julián", "Luciana", "Tomás",
    "Paula", "Andrés", "Antonella", "Felipe", "Juliana", "Emilio", "Manuela", "Esteban",
    "Salomé", "Simón", "Laura", "Martín", "Natalia", "Joaquín", "Verónica", "Ricardo",
    "Lorena", "Mauricio", "Catalina", "Hernán", "Diana", "Fabián", "Paola", "Gustavo",
]
LAST_NAMES = [
    "Arango", "Betancur", "Cardona", "Duque", "Echeverri", "Franco", "Giraldo", "Henao",
    "Isaza", "Jaramillo", "Londoño", "Marín", "Naranjo", "Ocampo", "Posada", "Quintero",
    "Restrepo", "Salazar", "Toro", "Uribe", "Valencia", "Zuluaga", "Villegas", "Mejía",
    "Correa", "Gallego", "Hoyos", "Montoya", "Osorio", "Rendón",
]
STREET_TYPES = ["Calle", "Carrera", "Avenida", "Diagonal", "Transversal"]

# (name, nit, slug, color, [parent categories it cares about])
ENTITIES = [
    ("Secretaría de Obras Públicas", "890.801.101-1", "obras", "#f59e0b", ["Infraestructura vial", "Gestión del riesgo"]),
    ("Aguas del Cumanday E.S.P.", "810.002.345-7", "aguas", "#0ea5e9", ["Servicios públicos", "Medio ambiente"]),
    ("Corporación Verde Andina", "900.345.678-2", "verdeandina", "#22c55e", ["Medio ambiente"]),
    ("Fundación Barrios Unidos", "901.234.567-9", "barriosunidos", "#a855f7", ["Seguridad", "Servicios públicos"]),
    ("Instituto de Movilidad Urbana", "890.456.789-3", "movilidad", "#6366f1", ["Movilidad", "Infraestructura vial"]),
    ("Cuerpo de Bomberos Voluntarios", "890.567.890-4", "bomberos", "#ef4444", ["Gestión del riesgo"]),
    ("Secretaría de Seguridad Ciudadana", "890.678.901-5", "seguridad", "#64748b", ["Seguridad"]),
    ("Constructora Altos del Ruiz S.A.S.", "901.789.012-6", "altosdelruiz", "#14b8a6", ["Infraestructura vial", "Movilidad"]),
]

OFFICIAL_ROLES = [
    "Inspector de obras", "Gestor territorial", "Técnico ambiental", "Coordinador de movilidad",
    "Analista de riesgo", "Promotor comunitario", "Supervisor de servicios",
]

# parent -> (color, description, [(subcategory, description, [annotation texts])])
CATEGORIES = {
    "Infraestructura vial": ("#f59e0b", "Estado de vías, andenes y señalización.", [
        ("Huecos en la vía", "Baches y hundimientos en la calzada.", [
            "Hueco profundo en el carril derecho, los carros frenan de golpe.",
            "Hundimiento de la calzada frente al paradero, crece con cada lluvia.",
            "Varios baches seguidos en la subida, ya hubo una moto accidentada.",
        ]),
        ("Andenes deteriorados", "Andenes rotos o sin continuidad.", [
            "Andén levantado por raíces, las personas mayores tienen que bajarse a la calle.",
            "Tramo de andén sin terminar, no hay paso para coches de bebé ni sillas de ruedas.",
            "Loza del andén partida y suelta frente a la tienda de la esquina.",
        ]),
        ("Señalización", "Señales de tránsito faltantes o dañadas.", [
            "El pare de la esquina está caído desde hace un mes.",
            "Falta la cebra peatonal frente a la escuela.",
            "Señal de velocidad tapada por la vegetación.",
        ]),
    ]),
    "Servicios públicos": ("#0ea5e9", "Alumbrado, acueducto, alcantarillado y aseo.", [
        ("Alumbrado público", "Luminarias apagadas o intermitentes.", [
            "Tres postes seguidos sin luz, la cuadra queda totalmente oscura.",
            "Luminaria que prende y apaga toda la noche.",
            "El parque no tiene alumbrado después de las 7 p. m.",
        ]),
        ("Acueducto y alcantarillado", "Fugas, tapas y desbordes.", [
            "Fuga de agua constante desde la tubería del andén.",
            "Alcantarilla sin tapa, es un riesgo para peatones.",
            "El alcantarillado se desborda cada vez que llueve fuerte.",
        ]),
        ("Recolección de basuras", "Frecuencia y puntos de recolección.", [
            "El carro recolector no pasa desde hace una semana.",
            "Las canecas públicas están llenas y rotas.",
            "Los vecinos piden un nuevo horario de recolección.",
        ]),
    ]),
    "Medio ambiente": ("#22c55e", "Árboles, quebradas y residuos.", [
        ("Árboles en riesgo", "Árboles inclinados, secos o sobre redes.", [
            "Árbol muy inclinado sobre las cuerdas de energía.",
            "Eucalipto seco que puede caer sobre las casas.",
            "Ramas grandes que tapan la vía después del viento.",
        ]),
        ("Contaminación de quebradas", "Vertimientos y basura en cauces.", [
            "Vertimiento de aguas negras a la quebrada, huele muy mal.",
            "Escombros arrojados en el cauce de la quebrada.",
            "La quebrada tiene espuma y color extraño desde ayer.",
        ]),
        ("Puntos críticos de residuos", "Botaderos a cielo abierto.", [
            "Botadero de escombros y colchones en el lote baldío.",
            "Acumulación de basura en la esquina, llegan roedores.",
            "Llantas abandonadas acumulando agua.",
        ]),
    ]),
    "Seguridad": ("#a855f7", "Convivencia y percepción de seguridad.", [
        ("Zonas inseguras", "Lugares con reportes de hurto.", [
            "Hurtos frecuentes en el sendero peatonal al anochecer.",
            "Los estudiantes reportan robos camino al colegio.",
            "Callejón sin iluminación ni vigilancia.",
        ]),
        ("Cámaras requeridas", "Solicitudes de videovigilancia.", [
            "La comunidad solicita una cámara en la entrada del barrio.",
            "La cámara existente no funciona desde hace meses.",
            "Se pide videovigilancia en el parque infantil.",
        ]),
        ("Presencia policial", "Solicitudes de patrullaje.", [
            "Se solicitan rondas policiales en la noche.",
            "El CAI más cercano no responde a los llamados.",
            "Riñas frecuentes los fines de semana en la cancha.",
        ]),
    ]),
    "Movilidad": ("#6366f1", "Transporte público, ciclorrutas y tráfico.", [
        ("Transporte público", "Rutas, paraderos y frecuencia.", [
            "El paradero no tiene techo ni bancas.",
            "La ruta de bus pasa cada 40 minutos en hora pico.",
            "Se pide ampliar el horario del cable aéreo.",
        ]),
        ("Ciclorrutas", "Infraestructura para bicicletas.", [
            "La ciclorruta está invadida por carros parqueados.",
            "Falta la conexión de la ciclorruta con la avenida.",
            "Separadores de la ciclorruta rotos.",
        ]),
        ("Congestión vehicular", "Trancones y puntos críticos.", [
            "Trancón diario en la glorieta entre 6 y 8 a. m.",
            "Parqueo en doble fila frente al colegio.",
            "El semáforo tiene tiempos muy cortos para el giro.",
        ]),
    ]),
    "Gestión del riesgo": ("#ef4444", "Deslizamientos, inundaciones y estabilidad.", [
        ("Deslizamientos", "Taludes inestables y movimientos en masa.", [
            "Grietas en el talud detrás de las casas después de las lluvias.",
            "Pequeño deslizamiento que tapó media vía.",
            "Árboles inclinándose en la ladera, posible movimiento de tierra.",
        ]),
        ("Inundaciones", "Encharcamientos y desbordes.", [
            "La calle se inunda con cualquier aguacero.",
            "Sumideros tapados causan encharcamientos grandes.",
            "El agua entró a varias viviendas en la última lluvia.",
        ]),
        ("Muros de contención", "Muros agrietados o faltantes.", [
            "Muro de contención con grietas visibles.",
            "El muro se está inclinando hacia la vía.",
            "Se requiere un muro en el borde de la cañada.",
        ]),
    ]),
}

VOTE_COMMENTS = {
    1: ["No es prioritario para el barrio.", "Ya se había solucionado antes."],
    2: ["Hay problemas más urgentes.", "Afecta poco pero existe."],
    3: ["Importante, pero puede esperar.", "Lo vemos a diario."],
    4: ["Muy importante arreglarlo pronto.", "Afecta a muchas familias.", "Totalmente de acuerdo."],
    5: ["¡Urgente! Es un peligro.", "Llevamos meses esperando solución.", "Prioridad para la comunidad."],
}
STAR_WEIGHTS = [1, 2, 4, 6, 7]

UPLOAD_ROOT = None  # set once the app config is loaded


# ── helpers ────────────────────────────────────────────────────────────────


def fetch_json(url):
    req = Request(url, headers={"User-Agent": "territorial-backend-seed/1.0"})
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).casefold()


def slug(text):
    return "".join(c if c.isalnum() else "." for c in normalize(text)).strip(".")


def random_date(rng, days_back, after=None):
    start = after or REFERENCE_DATE - timedelta(days=days_back)
    span = max((REFERENCE_DATE - start).total_seconds(), 60)
    return start + timedelta(seconds=rng.uniform(0, span))


def phone(rng):
    return f"3{rng.randint(0, 2)}{rng.randint(0, 9)}{rng.randint(1000000, 9999999)}"


def address(rng):
    return f"{rng.choice(STREET_TYPES)} {rng.randint(10, 80)} # {rng.randint(5, 99)}-{rng.randint(1, 99):02d}"


def write_svg(folder, filename, content):
    target = Path(UPLOAD_ROOT) / folder
    target.mkdir(parents=True, exist_ok=True)
    data = content.encode("utf-8")
    (target / filename).write_bytes(data)
    return f"/api/images/{folder}/{filename}", len(data)


def initials(name):
    words = [w for w in name.replace(".", " ").split() if w[0].isupper()]
    return "".join(w[0] for w in words[:2]) or name[:2].upper()


def logo_svg(name, color):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
        f'<rect width="256" height="256" rx="48" fill="{color}"/>'
        '<circle cx="200" cy="56" r="80" fill="#ffffff" opacity="0.12"/>'
        '<text x="128" y="150" font-family="Arial, sans-serif" font-size="96" font-weight="700" '
        f'fill="#ffffff" text-anchor="middle">{escape(initials(name))}</text></svg>'
    )


def category_svg(name, color):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
        f'<circle cx="128" cy="128" r="120" fill="{color}"/>'
        '<circle cx="128" cy="128" r="84" fill="#ffffff" opacity="0.18"/>'
        '<text x="128" y="152" font-family="Arial, sans-serif" font-size="72" font-weight="700" '
        f'fill="#ffffff" text-anchor="middle">{escape(initials(name))}</text></svg>'
    )


def evidence_svg(rng, title, description, color):
    hills = "".join(
        f'<ellipse cx="{rng.randint(0, 640)}" cy="{rng.randint(330, 420)}" rx="{rng.randint(120, 260)}" '
        f'ry="{rng.randint(50, 110)}" fill="{color}" opacity="{rng.uniform(0.25, 0.55):.2f}"/>'
        for _ in range(4)
    )
    caption = escape(description if len(description) <= 70 else description[:67] + "...")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="420" viewBox="0 0 640 420">'
        '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#0f172a"/>'
        f'<stop offset="1" stop-color="{color}"/></linearGradient></defs>'
        '<rect width="640" height="420" fill="url(#sky)"/>'
        f'<circle cx="{rng.randint(80, 560)}" cy="{rng.randint(50, 120)}" r="34" fill="#fde68a" opacity="0.8"/>'
        f"{hills}"
        '<rect x="0" y="340" width="640" height="80" fill="#0f172a" opacity="0.72"/>'
        f'<text x="24" y="372" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#ffffff">{escape(title)}</text>'
        f'<text x="24" y="400" font-family="Arial, sans-serif" font-size="15" fill="#e2e8f0">{caption}</text></svg>'
    )


def polygon_around(rng, center):
    """Irregular star-shaped polygon (6-8 vertices) that stays inside POLYGON_RADIUS."""
    lat, lng = center
    count = rng.randint(6, 8)
    step = 2 * math.pi / count
    start = rng.uniform(0, step)
    vertices = []
    for index in range(count):
        angle = start + index * step + rng.uniform(-0.15, 0.15) * step
        radius = POLYGON_RADIUS * rng.uniform(0.75, 1.0)
        vertices.append((lat + radius * math.sin(angle), lng + radius * math.cos(angle)))
    return vertices


def point_inside(rng, center):
    """Random point within 0.45 * radius: always inside the polygon (inradius >= ~0.57 * radius)."""
    angle = rng.uniform(0, 2 * math.pi)
    distance = POLYGON_RADIUS * 0.45 * math.sqrt(rng.random())
    return center[0] + distance * math.sin(angle), center[1] + distance * math.cos(angle)


class PersonFactory:
    """Invented, unique person names and example.com e-mails."""

    def __init__(self, rng):
        self.rng = rng
        self.used_names = set()
        self.used_emails = {"admin@example.com", "funcionario@example.com", "ciudadano@example.com"}

    def create(self):
        while True:
            name = f"{self.rng.choice(FIRST_NAMES)} {self.rng.choice(LAST_NAMES)} {self.rng.choice(LAST_NAMES)}"
            if name not in self.used_names:
                break
        self.used_names.add(name)
        first, last = name.split()[:2]
        base = f"{slug(first)}.{slug(last)}"
        email = f"{base}@{EMAIL_DOMAIN}"
        suffix = 2
        while email in self.used_emails:
            email = f"{base}{suffix}@{EMAIL_DOMAIN}"
            suffix += 1
        self.used_emails.add(email)
        return name, email


# ── seed steps ─────────────────────────────────────────────────────────────


def seed_departments_and_cities():
    try:
        departments_data = fetch_json(f"{API_COLOMBIA_BASE_URL}/Department")
        cities_data = fetch_json(f"{API_COLOMBIA_BASE_URL}/City")
    except Exception as error:  # noqa: BLE001 - any network failure falls back to offline data
        print(f"API Colombia no disponible ({error}); usando datos offline.")
        return seed_offline_departments()

    departments_by_api_id = {}
    for department_data in departments_data:
        departments_by_api_id[department_data["id"]] = Department(
            name=department_data["name"].strip(),
            dane_code=f"{int(department_data['id']):02d}",
        )
    db.session.add_all(departments_by_api_id.values())
    db.session.flush()

    seen_cities = set()
    cities = []
    for city_data in cities_data:
        department = departments_by_api_id.get(city_data.get("departmentId"))
        city_name = (city_data.get("name") or "").strip()
        if not department or not city_name:
            continue
        dedupe_key = (department.id_department, city_name.casefold())
        if dedupe_key in seen_cities:
            continue
        seen_cities.add(dedupe_key)
        cities.append(City(id_department=department.id_department, name=city_name,
                           dane_code=f"{int(city_data['id']):05d}"))
    db.session.add_all(cities)
    db.session.flush()
    return list(departments_by_api_id.values()), cities


def seed_offline_departments():
    departments, cities = [], []
    for name, dane_code, city_rows in OFFLINE_DEPARTMENTS:
        department = Department(name=name, dane_code=dane_code)
        db.session.add(department)
        db.session.flush()
        departments.append(department)
        for city_name, city_code in city_rows:
            cities.append(City(id_department=department.id_department, name=city_name, dane_code=city_code))
    db.session.add_all(cities)
    db.session.flush()
    return departments, cities


def find_city(cities, name):
    wanted = normalize(name)
    city = next((c for c in cities if normalize(c.name) == wanted), None)
    if city is None:
        raise RuntimeError(f"No se encontró la ciudad {name} para sembrar el territorio.")
    return city


def seed_territory(rng, cities):
    """Communes, neighborhoods and polygon vertices. Returns [(neighborhood, center)]."""
    neighborhoods = []
    points = []
    for city_name, (origin_lat, origin_lng), columns, communes in TERRITORY:
        city = find_city(cities, city_name)
        cell = 0
        for commune_index, (commune_name, neighborhood_names) in enumerate(communes):
            commune = Commune(id_city=city.id_city, name=commune_name,
                              status="inactive" if commune_index == len(communes) - 1 and len(communes) > 5 else "active")
            db.session.add(commune)
            db.session.flush()
            for neighborhood_name in neighborhood_names:
                row, column = divmod(cell, columns)
                cell += 1
                center = (
                    origin_lat - row * GRID_SPACING + rng.uniform(-CENTER_JITTER, CENTER_JITTER),
                    origin_lng + column * GRID_SPACING + rng.uniform(-CENTER_JITTER, CENTER_JITTER),
                )
                neighborhood = Neighborhood(id_commune=commune.id_commune, name=neighborhood_name,
                                            status="active" if rng.random() > 0.08 else "inactive")
                db.session.add(neighborhood)
                db.session.flush()
                for order, (lat, lng) in enumerate(polygon_around(rng, center), start=1):
                    points.append(Point(id_neighborhood=neighborhood.id_neighborhood, latitude=round(lat, 6),
                                        longitude=round(lng, 6), order=order, point_type="vertex"))
                neighborhoods.append((neighborhood, center))
    db.session.add_all(points)
    db.session.flush()
    return neighborhoods, len(points)


def seed_entities(rng):
    entities = []
    for name, nit, entity_slug, color, _ in ENTITIES:
        logo_url, _ = write_svg("logos", f"{entity_slug}.svg", logo_svg(name, color))
        entities.append(Entity(name=name, nit=nit, phone=f"(606) 8{rng.randint(10, 99)} {rng.randint(10, 99)} {rng.randint(10, 99)}",
                               email=f"contacto.{entity_slug}@{EMAIL_DOMAIN}", address=address(rng),
                               logo_url=logo_url, status="active" if entity_slug != "altosdelruiz" else "inactive"))
    db.session.add_all(entities)
    db.session.flush()
    return entities


def seed_officials(rng, people, entities, neighborhoods):
    officials = [
        Official(id_entity=entities[0].id_entity, name="Administrador Demo", email=f"admin@{EMAIL_DOMAIN}",
                 phone=phone(rng), role="admin", status="active", gps_active=False),
        Official(id_entity=entities[0].id_entity, name="Funcionario Demo", email=f"funcionario@{EMAIL_DOMAIN}",
                 phone=phone(rng), role="Gestor territorial", status="active", gps_active=True),
    ]
    for index in range(20):
        name, email = people.create()
        officials.append(Official(
            id_entity=entities[index % len(entities)].id_entity, name=name, email=email, phone=phone(rng),
            role="admin" if index == 0 else rng.choice(OFFICIAL_ROLES),
            status="active" if rng.random() > 0.1 else "inactive", gps_active=rng.random() < 0.6,
        ))
    for official in officials:
        lat, lng = point_inside(rng, rng.choice(neighborhoods)[1])
        official.last_latitude, official.last_longitude = round(lat, 6), round(lng, 6)
        hours_back = rng.uniform(0.05, 2) if official.gps_active else rng.uniform(6, 96)
        official.last_gps_update = REFERENCE_DATE - timedelta(hours=hours_back)
    db.session.add_all(officials)
    db.session.flush()
    return officials


def seed_citizens(rng, people, neighborhoods):
    citizens = [Citizen(name="Ciudadano Demo", email=f"ciudadano@{EMAIL_DOMAIN}", phone=phone(rng),
                        address=address(rng), status="active")]
    for _ in range(45):
        name, email = people.create()
        citizens.append(Citizen(name=name, email=email, phone=phone(rng), address=address(rng),
                                status="active" if rng.random() > 0.07 else "inactive"))
    for citizen in citizens:
        lat, lng = point_inside(rng, rng.choice(neighborhoods)[1])
        citizen.latitude, citizen.longitude = round(lat, 6), round(lng, 6)
    db.session.add_all(citizens)
    db.session.flush()
    return citizens


def seed_categories():
    """Returns [(parent_name, color, subcategory, texts)]."""
    subcategories = []
    for parent_name, (color, description, children) in CATEGORIES.items():
        image_url, _ = write_svg("categories", f"{slug(parent_name)}.svg", category_svg(parent_name, color))
        parent = Category(name=parent_name, description=description, image_url=image_url, status="active")
        db.session.add(parent)
        db.session.flush()
        for child_name, child_description, texts in children:
            image_url, _ = write_svg("categories", f"{slug(child_name)}.svg", category_svg(child_name, color))
            child = Category(id_parent_category=parent.id_category, name=child_name,
                             description=child_description, image_url=image_url, status="active")
            db.session.add(child)
            subcategories.append((parent_name, color, child, texts))
    db.session.flush()
    return subcategories


def seed_annotations(rng, neighborhoods, citizens, subcategories, entities):
    active_citizens = [c for c in citizens if c.status == "active"]
    # Busy neighborhoods get more reports so heatmaps and reports look realistic.
    weights = [rng.choice([1, 1, 2, 3, 5]) for _ in neighborhoods]
    counts = {"annotations": 0, "annotation_categories": 0, "interested_parties": 0, "votes": 0, "evidences": 0}
    evidence_number = 0

    for _ in range(170):
        neighborhood, center = rng.choices(neighborhoods, weights=weights)[0]
        parent_name, color, subcategory, texts = rng.choice(subcategories)
        lat, lng = point_inside(rng, center)
        created = random_date(rng, 365)
        description = rng.choice(texts)
        annotation = Annotation(id_neighborhood=neighborhood.id_neighborhood,
                                id_citizen=rng.choice(active_citizens).id_citizen, description=description,
                                latitude=round(lat, 6), longitude=round(lng, 6),
                                status="active" if rng.random() > 0.15 else "inactive", registration_date=created)
        db.session.add(annotation)
        db.session.flush()
        counts["annotations"] += 1

        category_ids = {subcategory.id_category}
        if rng.random() < 0.25:
            category_ids.add(rng.choice(subcategories)[2].id_category)
        for category_id in category_ids:
            db.session.add(AnnotationCategory(id_category=category_id, id_annotation=annotation.id_annotation))
        counts["annotation_categories"] += len(category_ids)

        related = [e for e, row in zip(entities, ENTITIES) if parent_name in row[4]]
        for entity in rng.sample(related, k=min(len(related), rng.randint(0, 2))):
            db.session.add(InterestedParty(id_entity=entity.id_entity, id_annotation=annotation.id_annotation,
                                           association_date=random_date(rng, 0, after=created)))
            counts["interested_parties"] += 1

        for voter in rng.sample(active_citizens, k=rng.randint(0, 6)):
            stars = rng.choices(range(1, 6), weights=STAR_WEIGHTS)[0]
            db.session.add(Vote(id_citizen=voter.id_citizen, id_annotation=annotation.id_annotation, stars=stars,
                                comment=rng.choice(VOTE_COMMENTS[stars]) if rng.random() > 0.2 else None,
                                vote_date=random_date(rng, 0, after=created)))
            counts["votes"] += 1

        for _ in range(rng.randint(1, 2)):
            evidence_number += 1
            file_url, size = write_svg("evidences", f"evidencia-{evidence_number:04d}.svg",
                                       evidence_svg(rng, f"{subcategory.name} · {neighborhood.name}", description, color))
            db.session.add(Evidence(id_annotation=annotation.id_annotation, file_url=file_url,
                                    file_type="image/svg+xml", file_size=size,
                                    upload_date=random_date(rng, 0, after=created)))
            counts["evidences"] += 1

    db.session.flush()
    return counts


def main():
    global UPLOAD_ROOT
    rng = random.Random(RANDOM_SEED)
    app = create_app()

    with app.app_context():
        UPLOAD_ROOT = Path(app.config["UPLOAD_FOLDER"])
        if not UPLOAD_ROOT.is_absolute():
            UPLOAD_ROOT = Path(app.root_path).parent / UPLOAD_ROOT

        db.drop_all()
        db.create_all()

        departments, cities = seed_departments_and_cities()
        neighborhoods, point_count = seed_territory(rng, cities)
        people = PersonFactory(rng)
        entities = seed_entities(rng)
        officials = seed_officials(rng, people, entities, neighborhoods)
        citizens = seed_citizens(rng, people, neighborhoods)
        subcategories = seed_categories()
        counts = seed_annotations(rng, neighborhoods, citizens, subcategories, entities)
        db.session.commit()

        summary = {
            "departments": len(departments),
            "cities": len(cities),
            "communes": Commune.query.count(),
            "neighborhoods": len(neighborhoods),
            "points": point_count,
            "entities": len(entities),
            "officials": len(officials),
            "citizens": len(citizens),
            "categories": Category.query.count(),
            **counts,
        }
        print("Demo seed OK:")
        for table, count in summary.items():
            print(f"  {table:<22}{count}")
        print(f"Imágenes en: {UPLOAD_ROOT}")
        print("Cuentas demo: admin@example.com, funcionario@example.com, ciudadano@example.com")
        print("Crear logins Firebase: FIREBASE_API_KEY=<web api key> python scripts/seed_firebase_users.py")


if __name__ == "__main__":
    main()
