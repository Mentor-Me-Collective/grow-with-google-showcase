from typing import Any
from sqlalchemy.exc import IntegrityError


from lib.extensions import db
from lib.models import EvidenceType

class EvidenceTypeRepository(object):
    @staticmethod
    def get_all() -> list[EvidenceType]:
        return EvidenceType.query.order_by(EvidenceType.name.asc()).all()

    @staticmethod
    def get_by_id(evidence_type_id: int) -> EvidenceType | None:
        return EvidenceType.query.get(evidence_type_id)

    @staticmethod
    def create(data: dict[str, Any]) -> EvidenceType:
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        evidence_type = EvidenceType(name=name)

        try:
            db.session.add(evidence_type)
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("EvidenceType already exists")
        return evidence_type

    @staticmethod
    def update(evidence_type: EvidenceType , data: dict[str, Any]) -> EvidenceType:
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        evidence_type.name = name
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("EvidenceType already exists")
        return evidence_type

    @staticmethod
    def get_by_name(evidence_type_name: str) -> EvidenceType | None:
        return EvidenceType.query.filter(EvidenceType.name == evidence_type_name).first()

    @staticmethod
    def delete(evidence_type: EvidenceType) -> None:
        db.session.delete(evidence_type)
        db.session.commit()

