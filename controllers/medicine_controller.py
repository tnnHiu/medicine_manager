from flask import  render_template
from datetime import datetime
from models.medicine import Medicine
from controllers.auth_controller import login_required, role_required


def register_medicine_routes(app):
    @app.route('/medicines', endpoint='medicines')
    @login_required
    def medicines():
        medicines_list = Medicine.query.all()
        current_date = datetime.now()
        return render_template('medicines.html',
                               medicines=medicines_list,
                               current_date=current_date)
