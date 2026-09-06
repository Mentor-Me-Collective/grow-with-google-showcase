from lib.extensions import db
from datetime import datetime, timezone

class Plant(db.Model):
    __tablename__ = 'plants'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scientificName = db.Column(db.String, nullable=False)
    species = db.Column(db.String, nullable=False)
    family = db.Column(db.String, nullable=False)
    genus = db.Column(db.String, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    long = db.Column(db.Float, nullable=False)
    eventDate = db.Column(db.Date, nullable=False)
    targetTaxonName = db.Column(db.String, nullable=False)
    evidenceTypeId = db.Column(db.Integer, db.ForeignKey('evidence_types.id'), nullable=False)
    pollinatorId = db.Column(db.Integer, db.ForeignKey('pollinators.id'), nullable=False)
    locates = db.relationship('Locate', back_populates='plant', lazy='dynamic')
    pollinator = db.relationship('Pollinator', foreign_keys=[pollinatorId], back_populates='plants')
    evidenceType = db.relationship('EvidenceType', foreign_keys=[evidenceTypeId], back_populates='plants')
