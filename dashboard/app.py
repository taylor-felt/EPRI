import os
import requests
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash
from threading import Thread
import time

from .config import Config
from .models import db, User, RatePeriod, Threshold, LoadGroup, Appliance, get_active_rate_period

app = Flask(__name__)
app.config.from_object(Config)

socketio = SocketIO(app)
login_manager = LoginManager(app)


def create_app():
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['GET'])
@login_required
def index():
    rate = get_active_rate_period()
    threshold = Threshold.query.first()
    return render_template('index.html', rate=rate, threshold=threshold)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Admin access required')
        return redirect(url_for('index'))
    if request.method == 'POST':
        threshold_value = float(request.form['threshold'])
        thr = Threshold.query.first()
        if not thr:
            thr = Threshold(value=threshold_value)
            db.session.add(thr)
        else:
            thr.value = threshold_value
        db.session.commit()
        flash('Settings updated')
    threshold = Threshold.query.first()
    return render_template('admin.html', threshold=threshold)


def fetch_power():
    moving_avg = 0
    alpha = 0.5
    while True:
        url = app.config['EGAUGE_URL']
        power = 0
        if url:
            try:
                r = requests.get(url, timeout=2)
                power = float(r.json().get('power', 0))
            except Exception:
                power = 0
        moving_avg = alpha * power + (1 - alpha) * moving_avg
        rate = get_active_rate_period()
        threshold = Threshold.query.first()
        cost = 0
        if rate:
            # moving_avg is kW; convert to kWh for one hour equivalent cost
            cost = moving_avg * rate.rate
        socketio.emit('power_update', {
            'power': round(moving_avg, 2),
            'rate_color': rate.color if rate else 'gray',
            'rate_label': rate.label if rate else 'N/A',
            'cost': round(cost, 4),
            'threshold_exceeded': threshold and moving_avg > threshold.value
        })
        time.sleep(1)


def start_background_thread():
    thread = Thread(target=fetch_power)
    thread.daemon = True
    thread.start()


if __name__ == '__main__':
    create_app()
    start_background_thread()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
