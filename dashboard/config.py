import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dashboard.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EGAUGE_URL = os.environ.get('EGAUGE_URL')  # eGauge API endpoint
