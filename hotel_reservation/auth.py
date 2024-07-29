import functools

from flask import(
    Blueprint, g, redirect, render_template, request, session, url_for
)

from hotel_reservation.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        age = request.form['age']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
            print_auth_result(error, username, age)
            return render_template('auth/error.html', error=error)
        elif not age:
            error = 'Age is required.'


        if error is not None:
            print_auth_result(error, username, age)
            return render_template('auth/error.html', error=error)
        else:
            try:
                age = int(age)
                db.execute(
                    'INSERT INTO user (username, age) VALUES (?, ?)',
                    (username, age),
                )
                db.commit()
            except db.IntegrityError:
                error = f'User {username} and age {age} is already registered.'
                print_auth_result(error, username, age)
                return render_template('auth/error.html', error=error)
            else:
                print_auth_result(error, username, age)
                return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        age = int(request.form['age'])
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ? AND age = ?', (username, age)
        ).fetchone()

        if user is None:
            error = 'Incorrect username or age.'
            print_auth_result(error, username, age)
            return render_template('auth/error.html', error=error)

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('reservation.index'))

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('reservation.index'))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)
    return wrapped_view

def print_auth_result(error, username, age):
    if error is not None:
        print(error)
    else:
        print('Succeeded.')
    print(f'username: {username}, age: {age}')
