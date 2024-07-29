from flask import (
    Blueprint, make_response, jsonify, current_app
)

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

from hotel_reservation.model.user import User

bp = Blueprint('user', __name__)

@bp.route('/')
def index():
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
    Session = sessionmaker(bind=engine)

    with Session.begin() as db_session:
        response = db_session.query(User).all()
        users = [{'id': user.id, 'username': user.username, 'age': user.age} for user in response]
        return make_response(jsonify(users), 200)
