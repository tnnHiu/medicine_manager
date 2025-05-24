from controllers.auth_controller import register_auth_routes
from controllers.patient_controller import register_patient_routes
from controllers.medicine_controller import register_medicine_routes
from controllers.user_controller import register_user_routes


def register_all_routes(app):
    register_auth_routes(app)
    register_patient_routes(app)
    register_medicine_routes(app)
    register_user_routes(app)
