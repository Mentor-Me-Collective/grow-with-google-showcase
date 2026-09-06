from typing import Any
from sqlalchemy.exc import IntegrityError


from lib.extensions import db
from lib.models import State

class StateRepository(object):
    @staticmethod
    def get_all() -> list[State]:
        return State.query.order_by(State.name.asc()).all()

    @staticmethod
    def get_by_name(state_name: str) -> State | None:
        return State.query.filter(State.name == state_name).first()

    @staticmethod
    def get_by_id(state_id: int) -> State | None:
        return State.query.get(state_id)

    @staticmethod
    def create(data: dict[str, Any]) -> State:
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        state = State(name=name)

        try:
            db.session.add(state)
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("State already exists")
        return state

    @staticmethod
    def update(state: State , data: dict[str, Any]) -> State:
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        state.name = name
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ValueError("State already exists")
        return state

    @staticmethod
    def delete(state: State) -> None:
        db.session.delete(state)
        db.session.commit()

