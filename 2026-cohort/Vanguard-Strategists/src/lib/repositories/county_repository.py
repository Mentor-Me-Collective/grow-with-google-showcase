from typing import Any
from sqlalchemy.exc import IntegrityError


from lib.extensions import db
from lib.models import County, county


class CountyRepository(object):
    @staticmethod
    def get_all(state_id: int|None = None) -> list[County]:
        query = County.query
        if state_id is not None:
            query = query.filter(County.stateId == state_id)
        return query.order_by(County.name.asc()).all()
    
    @staticmethod
    def get_by_id(county_id: int) -> County | None:
        return County.query.get(county_id)

    @staticmethod
    def get_by_name(county_name: str) -> County | None:
        return County.query.filter(County.name == county_name).first()

    @staticmethod
    def create(data: dict[str, Any]) -> County:
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        state_id = int(data.get('stateId', 0))
        if state_id == 0:
            raise ValueError("State id is required")
        county = County(name=name, stateId=state_id)

        try:
            db.session.add(county)
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("County already exists")
        return county

    @staticmethod
    def update(county: County, data: dict[str, Any]) -> County:
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        state_id = int(data.get('stateId', 0))
        if state_id == 0:
            raise ValueError("State id is required")
        county.name = name
        county.stateId = state_id
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("County already exists")
        return county

    @staticmethod
    def delete(county: County) -> None:
        db.session.delete(county)
        db.session.commit()

