from datetime import datetime, timedelta

from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for, abort, current_app
)
from sqlalchemy import *
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from hotel_reservation.auth import login_required

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    age = Column(String, unique=True)

class Reservation(Base):
    __tablename__ = 'reservation'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    start_date = Column(Date)
    end_date = Column(Date)
    number_rooms = Column(Integer)

bp = Blueprint('reservation', __name__, url_prefix='/reservation')

@bp.route('/')
@login_required
def index():
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
    Session = sessionmaker(bind=engine)

    with Session.begin() as db_session:
        reservations = db_session.query(Reservation,
            Reservation.id, User.username, Reservation.start_date, Reservation.end_date, Reservation.number_rooms) \
            .join(User, Reservation.user_id == User.id) \
            .where(Reservation.user_id == g.user['id']) \
            .all()

    print(reservations)

    return render_template('reservation/index.html', reservations=reservations)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        start_date = request.form['start-date']
        end_date = request.form['end-date']
        number_rooms = request.form['number-rooms']
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
        Session = sessionmaker(bind=engine)

        with Session.begin() as db_session:
            reservations = db_session.query(Reservation,
                Reservation.number_rooms) \
                .where(Reservation.start_date >= datetime.today().date()) \
                .all()

        number_reserved_rooms = 0
        for reservation in reservations:
            number_reserved_rooms += int(reservation.number_rooms)
            if number_reserved_rooms + number_rooms > 10:
                error = f'Rooms are full.'

        if error is not None:
            print_reservation_result(error, start_date, end_date, number_rooms)
            return render_template('reservation/error.html', error=error)
        else:
            with Session.begin() as db_session:
                db_session.add(
                    Reservation(user_id=g.user['id'], start_date=start_date, end_date=end_date, number_rooms=number_rooms)
                )

            print_reservation_result(error, start_date, end_date, number_rooms)
            return redirect(url_for('reservation.index'))

    return render_template('reservation/create.html')

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
            abort(404, f"Reservation id {id} doesn't exist.")

    if reservation.user_id != g.user['id']:
        abort(403)

    return reservation

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    reservation = get_reservation(id)

    if request.method == 'POST':
        start_date = request.form['start-date']
        end_date = request.form['end-date']
        number_rooms = request.form['number-rooms']
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
        Session = sessionmaker(bind=engine)

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
            return render_template('reservation/error.html', error=error)
        else:
            with Session.begin() as db_session:
                reservation = db_session.query(Reservation) \
                    .where(Reservation.id == id) \
                    .one()

                reservation.start_date = start_date
                reservation.end_date = end_date
                reservation.number_rooms = number_rooms

            print_reservation_result(error, start_date, end_date, number_rooms)
            return redirect(url_for('reservation.index'))

    return render_template('reservation/update.html', reservation=reservation)


@bp.route('/search', methods=('GET', 'POST'))
@login_required
def search():
    if request.method == 'POST':
        error = None
        start_date = request.form['start-date']

        if not start_date:
            error = 'Start date is required.'

        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

        if error is not None:
            print_reservation_result(error, start_date, end_date, number_rooms)
            return render_template('reservation/error.html', error=error)
        else:
            engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
            Session = sessionmaker(bind=engine)

            with Session.begin() as db_session:
                reservations = db_session.query(Reservation,
                    Reservation.id, User.username, Reservation.start_date, Reservation.end_date, Reservation.number_rooms) \
                    .join(User, Reservation.user_id == User.id) \
                    .where(Reservation.user_id == g.user['id'], Reservation.start_date == start_date) \
                    .all()

            return render_template('reservation/index.html', reservations=reservations, title='Search result')

    return render_template('reservation/search.html')

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'], echo=True)
    Session = sessionmaker(bind=engine)

    with Session.begin() as db_session:
        db_session.query(Reservation) \
            .where(Reservation.id == id) \
            .delete()

    return redirect(url_for('reservation.index'))

def print_reservation_result(error, start_date, end_date, number_rooms):
    if error is not None:
        print(error)
    else:
        print('Succeeded.')
    print(f'start_date: {start_date}, end_date: {end_date}, number_rooms: {number_rooms}')
