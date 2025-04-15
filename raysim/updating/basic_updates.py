from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable
from uuid import UUID

from .base import AgentUpdate, SimUpdate

if TYPE_CHECKING:
    from ..agents.base_state import AgentState
    from ..simulation import SimState


@dataclass
class AttrUpdate(AgentUpdate):
    """Modify an immutable attribute for a state.

    Attributes:
        attr: The attribute to modify.
        value: The new value of the attribute.
    """
    attr: str
    value: Any

    def apply(self, context: 'AgentState'):
        """Apply this update to change an attribute of the agent state."""
        setattr(context, self.attr, self.value)
    
    def replacement(self, updates: Iterable['AttrUpdate']) -> None | tuple[int, 'AttrUpdate']:
        for i, update in enumerate(updates):
            if isinstance(update, AttrUpdate) and update.attr == self.attr:
                return i, self
        return None


@dataclass
class NumericUpdate(AgentUpdate):
    """Modify a numeric attribute for a state.

    Attributes:
        attr: The attribute to modify.
        delta: The amount to add to the attribute.
    """
    attr: str
    delta: int | float

    def apply(self, context: 'AgentState'):
        """Apply this update to change an attribute of the agent state."""
        current_value = getattr(context, self.attr)
        setattr(context, self.attr, current_value + self.delta)


@dataclass
class AgentAddUpdate(SimUpdate):
    """Add an agent to the simulation.

    Attributes:
        agent: The agent to add.
    """
    agent: 'AgentState'

    def apply(self, context: 'SimState'):
        context.add(self.agent)


@dataclass
class AgentRemoveUpdate(SimUpdate):
    """Remove an agent from the simulation.

    Attributes:
        agent_name: The name of the agent to remove.
    """
    agent_name: UUID

    def apply(self, context: 'SimState'):
        context.remove(context.by_name(self.agent_name))
