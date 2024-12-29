from flask import Blueprint, render_template, session
from config.db import db
from models.users import UserManager

error_bp = Blueprint('errors', __name__)
user_manager = UserManager(db)

@error_bp.app_errorhandler(404)
def page_not_found(error):
    user = user_manager.getUserBySession(session)
    return render_template('page_not_found.html', user=user), 404
