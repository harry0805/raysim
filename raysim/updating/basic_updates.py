from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
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
    priority = 0
    
    attr: str
    value: Any

    def apply(self, context: 'AgentState'):
        """Apply this update to change an attribute of the agent state."""        
        setattr(context, self.attr, self.value)
    
    @staticmethod
    def squash(updates: list['AttrUpdate']) -> list['AttrUpdate']:
        """Squash multiple AttrUpdate instances into a minimal set.
        
        When multiple AttrUpdate instances modify the same attribute,
        only the last one will have an effect. This method combines them
        into a single update with the final value for each attribute.
        """
        # Use OrderedDict to track attributes in order of first appearance
        attr_to_update = OrderedDict[str, AttrUpdate]()
        
        # Process updates in original order (last one overwrites previous ones)
        for update in updates:
            attr_to_update[update.attr] = update
        
        # Return values directly - OrderedDict maintains insertion order
        return list(attr_to_update.values())


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
