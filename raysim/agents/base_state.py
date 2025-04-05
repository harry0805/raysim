from dataclasses import dataclass, field
from typing import TYPE_CHECKING, dataclass_transform
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .base_agent import Agent


@dataclass_transform(field_specifiers=(field, ))
class StateMeta(type):
    """A metaclass for the AgentState class."""
    def __new__(cls, name, bases, namespace, **kwargs):
        # Every class with this metaclass must define a staticmethod agent()
        agent_func = namespace.get('agent', None)
        if not callable(agent_func):
            raise NotImplementedError(f"A staticmethod agent() must be defined in '{name}'.")
        data_cls = super().__new__(cls, name, bases, namespace, **kwargs)
        return dataclass(data_cls)  # type: ignore


class AgentState(metaclass=StateMeta):
    """A dataclass which stores all information about an agent.
    Use type annotations to define field types.
    `dataclasses.field` is also supported for default values and metadata.
    
    **Note**: Fields must be immutable types or an `AgentSet` object.
    """
    name: UUID = field(default_factory=uuid4, init=False)
    
    @staticmethod
    def agent() -> 'type[Agent]':
        """Returns the `Agent` class that this state belongs to."""
        from .base_agent import Agent
        return Agent


# class ExampleState(AgentState):
#     """An example state class."""
#     # Example fields
#     field1: int = field(default=0)
#     field2: str = field(default="")
#     field3: float = field(default=0.0)
#     field4: list[int] = field(default_factory=list)  # Example of a mutable type
    
#     # @staticmethod
#     # def agent():
#     #     from .base_agent import Agent
#     #     return Agent

# print(ExampleState().agent())