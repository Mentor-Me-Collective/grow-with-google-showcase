from typing import Any
from sqlalchemy.exc import IntegrityError


from lib.extensions import db
from lib.models import Pollinator


class PollinatorRepository(object):
    @staticmethod
    def get_all() -> list[Pollinator]:
        return Pollinator.query.order_by(Pollinator.name.asc()).all()

    @staticmethod
    def get_by_id(pollinator_id: int) -> Pollinator | None:
        return Pollinator.query.get(pollinator_id)

    @staticmethod
    def get_by_name(pollinator_name: str) -> Pollinator | None:
        return Pollinator.query.filter(Pollinator.name == pollinator_name).first()

    @staticmethod
    def create(data: dict[str, Any]) -> Pollinator:
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        pollinator = Pollinator(name=name)

        try:
            db.session.add(pollinator)
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("Pollinator already exists")
        return pollinator

    @staticmethod
    def update(pollinator: Pollinator, data: dict[str, Any]) -> Pollinator:
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        pollinator.name = name
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("Pollinator already exists")
        return pollinator

    @staticmethod
    def delete(pollinator: Pollinator) -> None:
        db.session.delete(pollinator)
        db.session.commit()

