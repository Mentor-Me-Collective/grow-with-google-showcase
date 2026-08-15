from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Wire(BaseModel):
    """Base for anything that crosses the wire.

    The contract is camelCase and Python is snake_case, so serialisation aliases
    are generated rather than written by hand on every field — one place to be
    wrong instead of several hundred.

    `populate_by_name` lets internal code build these with Python names while
    the JSON stays camelCase, and `from_attributes` lets them be built straight
    from SQLAlchemy rows.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        serialize_by_alias=True,
    )
