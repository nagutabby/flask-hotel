import functools

from flask import(
    Blueprint, g, request, session, url_for, current_app
)

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from hotel_reservation.db import get_db
from hotel_reservation.response import create_error_message, create_ok_message
from hotel_reservation.model.user import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('POST',))
def register():
    r = request.json
    username = r['username']
    age = r['age']
    db = get_db()
    error = None

    if not username:
        error = 'Username is required.'
    elif not age:
        error = 'Age is required.'

    if error is not None:
        print_auth_result(error, username, age)
        return create_error_message(error)
    else:
        try:
            age = int(age)

            engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
            Session = sessionmaker(bind=engine)

            with Session.begin() as db_session:
                db_session.add(User(username=username, age=age))

        except IntegrityError:
            error = f'User {username} and age {age} is already registered.'
            print_auth_result(error, username, age)
            return create_error_message(error)
        else:
            print_auth_result(error, username, age)
            return create_ok_message()

@bp.route('/login', methods=('POST',))
def login():
    r = request.json
    username = r['username']
    age = int(r['age'])
    error = None

    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session.begin() as db_session:
        user = db_session.query(User).where(User.username == username, User.age == age).one()
    if user is None:
        error = 'Incorrect username or age.'

    if error is not None:
        print_auth_result(error, username, age)
        return create_error_message(error)
    else:
        session.clear()
        session['user_id'] = user.id
        return create_ok_message()

@bp.route('/logout', methods=('DELETE',))
def logout():
    session.clear()
    return create_ok_message()

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
        Session = sessionmaker(bind=engine, expire_on_commit=False)

        with Session.begin() as db_session:
            g.user = db_session.query(User).where(User.id == user_id).one()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return create_error_message('You must be logged in.')

        return view(**kwargs)
    return wrapped_view

def print_auth_result(error, username, age):
    if error is not None:
        print(error)
    else:
        print('Succeeded.')
    print(f'username: {username}, age: {age}')
