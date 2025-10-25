from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String(80))
    seats_total = db.Column(db.Integer, default=100)
    seats_sold = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def seats_available(self):
        return max(self.seats_total - self.seats_sold, 0)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    buyer_name = db.Column(db.String(120))
    quantity = db.Column(db.Integer, default=1)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)

    movie = db.relationship('Movie', backref=db.backref('tickets', lazy=True))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)