from app.controllers.department_controller import bp as department_bp
from app.controllers.city_controller import bp as city_bp
from app.controllers.commune_controller import bp as commune_bp
from app.controllers.neighborhood_controller import bp as neighborhood_bp
from app.controllers.point_controller import bp as point_bp
from app.controllers.annotation_controller import bp as annotation_bp
from app.controllers.category_controller import bp as category_bp
from app.controllers.entity_controller import bp as entity_bp
from app.controllers.interested_party_controller import bp as interested_party_bp
from app.controllers.vote_controller import bp as vote_bp
from app.controllers.citizen_controller import bp as citizen_bp
from app.controllers.annotation_category_controller import bp as annotation_category_bp
from app.controllers.evidence_controller import bp as evidence_bp
from app.controllers.official_controller import bp as official_bp
from app.controllers.image_controller import bp as image_bp
from app.controllers.report_controller import bp as report_bp

def register_blueprints(app):
    app.register_blueprint(department_bp)
    app.register_blueprint(city_bp)
    app.register_blueprint(commune_bp)
    app.register_blueprint(neighborhood_bp)
    app.register_blueprint(point_bp)
    app.register_blueprint(annotation_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(entity_bp)
    app.register_blueprint(interested_party_bp)
    app.register_blueprint(vote_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(annotation_category_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(official_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(report_bp)
