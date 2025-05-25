from controllers.auth_controller import register_auth_routes
from controllers.patient_controller import register_patient_routes
from controllers.medicine_controller import register_medicine_routes
from controllers.user_controller import register_user_routes
from controllers.inventory_log_controller import register_inventory_log_routes
from controllers.medicine_batches_controller import register_medicine_batch_routes


def register_all_routes(app):
    register_auth_routes(app)
    register_patient_routes(app)
    register_medicine_routes(app)
    register_user_routes(app)
    register_inventory_log_routes(app)
    register_medicine_batch_routes(app)
