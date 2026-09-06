from lib.extensions import db
from datetime import datetime, timezone

class County(db.Model):
    __tablename__ = 'counties'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    stateId = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    state = db.relationship('State', foreign_keys=[stateId],back_populates='counties')
    locates = db.relationship('Locate',back_populates='county',lazy='dynamic')
