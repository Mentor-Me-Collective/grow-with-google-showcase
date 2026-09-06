from lib.extensions import db
from datetime import datetime, timezone

class EvidenceType(db.Model):
    __tablename__ = 'evidence_types'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    plants = db.relationship('Plant', back_populates='evidenceType')
