from lib.extensions import db
from datetime import datetime, timezone

class Locate(db.Model):
    __tablename__ = 'locates'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    countyId = db.Column(db.Integer, db.ForeignKey('counties.id'), nullable=False)
    plantId = db.Column(db.Integer, db.ForeignKey('plants.id'), nullable=False)
    stateId = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    plant = db.relationship('Plant', foreign_keys=[plantId],back_populates='locates')
    state = db.relationship('State', foreign_keys=[stateId], back_populates='locates')
    county = db.relationship('County', foreign_keys=[countyId], back_populates='locates')
