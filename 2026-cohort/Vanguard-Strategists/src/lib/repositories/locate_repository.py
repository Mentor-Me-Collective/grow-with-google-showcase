from typing import Any
from sqlalchemy.exc import IntegrityError


from lib.extensions import db
from lib.models import Locate, locate


class LocateRepository(object):
    @staticmethod
    def get_all(state_id: int|None = None, plant_id: int|None = None, county_id: int|None = None) -> list[Locate]:
        query = Locate.query
        if state_id is not None:
            query = query.filter(Locate.stateId == state_id)
        if plant_id is not None:
            query = query.filter(Locate.plantId == state_id)
        if county_id is not None:
            query = query.filter(Locate.countyId == state_id)
        return query.order_by(Locate.plantId.asc()).all()

    @staticmethod
    def get_by_id(locate_id: int) -> Locate | None:
        return Locate.query.get(locate_id)

    @staticmethod
    def create(data: dict[str, Any]) -> Locate:
        state_id = int(data.get('stateId', 0))
        if state_id == 0:
            raise ValueError("State id is required")
        plant_id = int(data.get('plantId', 0))
        if plant_id == 0:
            raise ValueError("Plant id is required")
        county_id = int(data.get('countyId', 0))
        if county_id == 0:
            raise ValueError("County id is required")
        locate = Locate(stateId=state_id, plantId=plant_id, countyId=county_id)

        try:
            db.session.add(locate)
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("Locate already exists")
        return locate

    @staticmethod
    def update(locate: Locate, data: dict[str, Any]) -> Locate:
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        state_id = int(data.get('stateId', 0))
        if state_id == 0:
            raise ValueError("State id is required")
        plant_id = int(data.get('plantId', 0))
        if plant_id == 0:
            raise ValueError("Plant id is required")
        county_id = int(data.get('countyId', 0))
        if county_id == 0:
            raise ValueError("County id is required")
        locate.name = name
        locate.stateId = state_id
        locate.plantId = plant_id
        locate.countyId = county_id
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("Locate already exists")
        return locate

    @staticmethod
    def delete(locate: Locate) -> None:
        db.session.delete(locate)
        db.session.commit()

