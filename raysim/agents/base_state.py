from dataclasses import dataclass, field, replace, asdict
from typing import dataclass_transform, Self
from uuid import UUID, uuid4

from ..mutable_fields import MutableBaseField


@dataclass_transform(field_specifiers=(field, ))
class StateMeta(type):
    """A metaclass for the AgentState class."""
    def __new__(cls, name, bases, namespace, **kwargs):
        data_cls = super().__new__(cls, name, bases, namespace, **kwargs)
        return dataclass(data_cls)  # type: ignore


class AgentState(metaclass=StateMeta):
    """A dataclass which stores all information about an agent.
    Use type annotations to define field types.
    `dataclasses.field` is also supported for default values and metadata.
    
    **Note**: Fields must be immutable types or a supported mutable field object.
    """
    name: UUID = field(default_factory=uuid4, init=False)
    
    def copy(self) -> Self:
        """Creates a copy of the current state."""
        state_copy = replace(self)
        for field, value in asdict(self).items():
            # If the field is mutable, create a copy of it
            if isinstance(value, MutableBaseField):
                setattr(state_copy, field, value.copy())
        return state_copy
