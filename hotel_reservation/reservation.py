from datetime import datetime, timedelta

from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for, abort
)
from sqlalchemy import *
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from hotel_reservation.auth import login_required
from hotel_reservation.db import get_db

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    age: Mapped[int] = mapped_column(Integer, unique=True)

class Reservation(Base):
    __tablename__ = 'reservation'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    start_date: Mapped[int] = mapped_column(Integer)
    end_date: Mapped[int] = mapped_column(Integer)
    number_rooms: Mapped[int] = mapped_column(Integer)

bp = Blueprint('reservation', __name__, url_prefix='/reservation')

@bp.route('/')
@login_required
def index():
    db = get_db()
    user_id = int(session['user_id'])
    reservations = db.execute(
        'SELECT r.id, u.username, start_date, end_date, number_rooms'
        ' FROM reservation r JOIN user u ON r.user_id = u.id'
        ' WHERE r.user_id = ?',
        (user_id,)
    ).fetchall()

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

        db = get_db()
        reservations = db.execute(
            "SELECT number_rooms FROM reservation"
            " WHERE start_date >= strftime('%m-%d-%Y', date('now'))"
        ).fetchall()
        number_reserved_rooms = 0
        for reservation in reservations:
            number_reserved_rooms += int(reservation['number_rooms'])
        if number_reserved_rooms + number_rooms > 10:
            error = f'Rooms are full.'

        if error is not None:
            print_reservation_result(error, start_date, end_date, number_rooms)
            return render_template('reservation/error.html', error=error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO reservation (user_id, start_date, end_date, number_rooms)'
                ' VALUES (?, ?, ?, ?)',
                (g.user['id'], start_date, end_date, number_rooms)
            )
            db.commit()
            print_reservation_result(error, start_date, end_date, number_rooms)
            return redirect(url_for('reservation.index'))

    return render_template('reservation/create.html')

def get_reservation(id):
    reservation = get_db().execute(
        'SELECT r.id, user_id, u.username, start_date, end_date, number_rooms'
        ' FROM reservation r JOIN user u ON r.user_id = u.id'
        ' WHERE r.id = ?',
        (id,)
    ).fetchone()

    if reservation is None:
        abort(404, f"Reservation id {id} doesn't exist.")

    if reservation['user_id'] != g.user['id']:
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

        db = get_db()
        reservations = db.execute(
            "SELECT number_rooms FROM reservation"
            " WHERE start_date >= strftime('%m-%d-%Y', date('now')) AND NOT id = ?",
            (id, )
        ).fetchall()
        number_reserved_rooms = 0
        for reservation in reservations:
            number_reserved_rooms += int(reservation['number_rooms'])
        if number_reserved_rooms + number_rooms > 10:
            error = f'Rooms are full.'

        if error is not None:
            print_reservation_result(error, start_date, end_date, number_rooms)
            return render_template('reservation/error.html', error=error)
        else:
            db = get_db()
            db.execute(
                'UPDATE reservation SET start_date = ?, end_date = ?, number_rooms = ?'
                ' WHERE id = ?',
                (start_date, end_date, number_rooms, id)
            )
            db.commit()
            print_reservation_result(error, start_date, end_date, number_rooms)
            return redirect(url_for('reservation.index'))

    return render_template('reservation/update.html', reservation=reservation)


@bp.route('/search', methods=('GET', 'POST'))
@login_required
def search():
    if request.method == 'POST':
        db = get_db()
        user_id = int(session['user_id'])

        start_date = request.form['start-date']

        reservations = db.execute(
            'SELECT r.id, u.username, start_date, end_date, number_rooms'
            ' FROM reservation r JOIN user u ON r.user_id = u.id'
            ' WHERE r.user_id = ? AND start_date = ?',
            (user_id, start_date)
        ).fetchall()

        return render_template('reservation/index.html', reservations=reservations)

    return render_template('reservation/search.html')

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    db = get_db()
    db.execute('DELETE FROM reservation WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('reservation.index'))

def print_reservation_result(error, start_date, end_date, number_rooms):
    if error is not None:
        print(error)
    else:
        print('Succeeded.')
    print(f'start_date: {start_date}, end_date: {end_date}, number_rooms: {number_rooms}')
