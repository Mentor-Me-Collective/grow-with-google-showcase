from lib.extensions import db
from datetime import datetime, timezone


class State(db.Model):
    __tablename__ = 'states'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    counties = db.relationship('County',back_populates='state',lazy='dynamic')
    locates = db.relationship('Locate', back_populates='state', lazy='dynamic')