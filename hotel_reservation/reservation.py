from datetime import datetime, timedelta

from flask import (
    Blueprint, g, request, session, url_for, abort, current_app, jsonify, make_response, Response
)

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from hotel_reservation.auth import login_required
from hotel_reservation.model.user import User
from hotel_reservation.model.reservation import Reservation
from hotel_reservation.response import create_error_message, create_ok_message

bp = Blueprint('reservation', __name__, url_prefix='/reservation')

@bp.route('/')
@login_required
def index():
    user_id = int(session['user_id'])
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session.begin() as db_session:
        response = db_session.query(Reservation) \
            .join(User, Reservation.user_id == User.id) \
            .where(Reservation.user_id == user_id) \
            .all()

    reservations = [
        {
            'id': reservation.id,
            'user_id': reservation.user_id,
            'start_date': reservation.start_date,
            'end_date': reservation.end_date,
            'num_rooms': reservation.number_rooms
        } for reservation in response]

    return make_response(jsonify(reservations), 200)


@bp.route('/create', methods=('POST',))
@login_required
def create():
    user_id = int(session['user_id'])
    r = request.json
    start_date = r['start_date']
    end_date = r['end_date']
    number_rooms = r['number_rooms']
    error = None

    if not start_date:
        error = 'Start date is required.'
    elif not end_date:
        error = 'End date is required.'
    elif not number_rooms:
        error = 'Number of the rooms is required.'

    number_rooms = int(number_rooms)

    if number_rooms < 1:
        error = 'Number of the rooms must be 1 or more.'

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    if end_date <= start_date:
        error = 'End date must be later than start date.'
    elif end_date > datetime.today().date() + timedelta(days=30):
        error = 'You can reserve the hotel up to 30 days.'

    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session.begin() as db_session:
        reservations = db_session.query(Reservation,
            Reservation.number_rooms) \
            .where(Reservation.start_date >= datetime.today().date()) \
            .all()

    number_reserved_rooms = 0
    for reservation in reservations:
        number_reserved_rooms += int(reservation.number_rooms)
        if number_reserved_rooms + number_rooms > 10:
            error = 'Rooms are full.'

    if error is not None:
        print_reservation_result(error, start_date, end_date, number_rooms)
        return create_error_message(error)
    else:
        with Session.begin() as db_session:
            db_session.add(
                Reservation(user_id=user_id, start_date=start_date, end_date=end_date, number_rooms=number_rooms)
            )

        print_reservation_result(error, start_date, end_date, number_rooms)
        return create_ok_message()

def get_reservation(id):
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
    Session = sessionmaker(bind=engine)

    with Session.begin() as db_session:
        try:
            reservation = db_session.query(Reservation,
                Reservation.id, Reservation.user_id, User.username, Reservation.start_date, Reservation.end_date, Reservation.number_rooms) \
               .join(User, Reservation.user_id == User.id) \
               .where(Reservation.id == id) \
               .one()
        except NoResultFound:
            error_message = {
                'error': f"Reservation id {id} doesn't exist."
            }
            return make_response(error_message, 404)

    if reservation.user_id != g.user.id:
        error_message = {
            'error': "You don't have the permission to see the reservation."
        }
        return make_response(error_message, 403)

    return reservation

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    response = get_reservation(id)
    if isinstance(response, Response):
        return response
    else:
        reservation = [
            {
                'id': response.id,
                'user_id': response.user_id,
                'start_date': response.start_date,
                'end_date': response.end_date,
                'num_rooms': response.number_rooms
            }
        ]

    if request.method == 'POST':
        r = request.json
        start_date = r['start_date']
        end_date = r['end_date']
        number_rooms = r['number_rooms']
        error = None

        if not start_date:
            error = 'Start date is required.'
        elif not end_date:
            error = 'End date is required.'
        elif not number_rooms:
            error = 'Number of the rooms is required.'

        number_rooms = int(number_rooms)

        if number_rooms < 1:
            error = 'Number of the rooms must be 1 or more.'

        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        if end_date <= start_date:
            error = 'End date must be later than start date.'
        elif end_date > datetime.today().date() + timedelta(days=30):
            error = 'You can reserve the hotel up to 30 days.'

        engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
        Session = sessionmaker(bind=engine, expire_on_commit=False)

        with Session.begin() as db_session:
            reservations = db_session.query(Reservation,
                Reservation.number_rooms) \
                .where(Reservation.start_date >= datetime.today().date(), not_(Reservation.id == id)) \
                .all()

        number_reserved_rooms = 0
        for reservation in reservations:
            number_reserved_rooms += int(reservation.number_rooms)
        if number_reserved_rooms + number_rooms > 10:
            error = f'Rooms are full.'

        if error is not None:
            print_reservation_result(error, start_date, end_date, number_rooms)
            return create_error_message(error)
        else:
            with Session.begin() as db_session:
                reservation = db_session.query(Reservation) \
                    .where(Reservation.id == id) \
                    .one()

                reservation.start_date = start_date
                reservation.end_date = end_date
                reservation.number_rooms = number_rooms

            print_reservation_result(error, start_date, end_date, number_rooms)
            return create_ok_message()

    return make_response(jsonify(reservation), 200)


@bp.route('/search', methods=('GET',))
@login_required
def search():
    user_id = int(session['user_id'])
    error = None
    r = request.args
    start_date = r['start_date']

    if not start_date:
        error = 'Start date is required.'

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    if error is not None:
        print_reservation_result(error, start_date, end_date, number_rooms)
        return create_error_message(error)
    else:
        engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
        Session = sessionmaker(bind=engine, expire_on_commit=False)

        with Session.begin() as db_session:
            response = db_session.query(Reservation) \
                .join(User, Reservation.user_id == User.id) \
                .where(Reservation.user_id == user_id, Reservation.start_date == start_date) \
                .all()

        reservations = [
            {
                'id': reservation.id,
                'user_id': reservation.user_id,
                'start_date': reservation.start_date,
                'end_date': reservation.end_date,
                'num_rooms': reservation.number_rooms
            } for reservation in response]

        return make_response(jsonify(reservations), 200)

@bp.route('/<int:id>/delete', methods=('DELETE',))
@login_required
def delete(id):
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
    Session = sessionmaker(bind=engine)

    with Session.begin() as db_session:
        db_session.query(Reservation) \
            .where(Reservation.id == id) \
            .delete()

    return create_ok_message()

def print_reservation_result(error, start_date, end_date, number_rooms):
    if error is not None:
        print(error)
    else:
        print('Succeeded.')
    print(f'start_date: {start_date}, end_date: {end_date}, number_rooms: {number_rooms}')
