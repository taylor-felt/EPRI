from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class RatePeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50))
    start_hour = db.Column(db.Integer)  # hour 0-23
    end_hour = db.Column(db.Integer)
    rate = db.Column(db.Float)  # cost per kWh
    color = db.Column(db.String(20))

class Threshold(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)  # kW

class LoadGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    color = db.Column(db.String(20))
    energy_this_month = db.Column(db.Float, default=0.0)  # kWh

class Appliance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    group_id = db.Column(db.Integer, db.ForeignKey('load_group.id'))
    group = db.relationship('LoadGroup', backref='appliances')

from datetime import datetime


def get_active_rate_period():
    now = datetime.now().hour
    return RatePeriod.query.filter(RatePeriod.start_hour <= now, RatePeriod.end_hour > now).first()
