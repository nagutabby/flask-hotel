from flask import (
    Blueprint, g, redirect, render_template, request, url_for
)

from hotel_reservation.auth import login_required
from hotel_reservation.db import get_db

bp = Blueprint('user', __name__)

@bp.route('/')
def index():
    db = get_db()
    users = db.execute(
        'SELECT username, age FROM user'
    ).fetchall()

    return render_template('user/index.html', users=users)
