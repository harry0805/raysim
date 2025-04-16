from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable
from uuid import UUID

from .base import Update, AgentUpdate, SimUpdate

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
    priority = 0
    
    attr: str
    value: Any

    def apply(self, context: 'AgentState'):
        """Apply this update to change an attribute of the agent state."""
        setattr(context, self.attr, self.value)
    
    @staticmethod
    def squash(updates: list[Update]) -> None:
        attr_updates = [u for u in updates if isinstance(u, AttrUpdate)]
        latest_updates = {}
        for update in attr_updates:
            latest_updates[update.attr] = update
        updates[:] = [u for u in updates if not isinstance(u, AttrUpdate)] + list(latest_updates.values())


@dataclass
class NumericUpdate(AgentUpdate):
    """Modify a numeric attribute for a state.

    Attributes:
        attr: The attribute to modify.
        delta: The amount to add to the attribute.
    """
    priority = 5
    
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
    priority = 101
    
    agent: 'AgentState'

    def apply(self, context: 'SimState'):
        context.add(self.agent)


@dataclass
class AgentRemoveUpdate(SimUpdate):
    """Remove an agent from the simulation.

    Attributes:
        agent_name: The name of the agent to remove.
    """
    priority = 100
    
    agent_name: UUID

    def apply(self, context: 'SimState'):
        context.remove(context.by_name(self.agent_name))
