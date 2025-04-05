from copy import deepcopy
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ..mutable_fields.base import MutableBaseField, MutableFieldProxy
from ..updating import AgentUpdate, AttrUpdate
from .base_state import AgentState

if TYPE_CHECKING:
    from ..simulation import SimAgents


class Agent:
    """The base class for all agents in the simulation."""
    all_agents: 'SimAgents'
    _state: AgentState
    _state_original: AgentState
    
    # Type hint for the type checker, those attributes are actually in AgentState
    name: UUID

    def __init__(self, state: AgentState, all_agents: 'SimAgents'):
        # Initially, the original state has the same reference as the copy to save memory.
        self._state = state
        self._state_original = state
        self.all_agents = all_agents

    def add_update(self, update: AgentUpdate):
        """Add an update to the simulation.
        
        This method should not be used directly in a simulation,
        updates are automatically added when an agent attribute is modified.
        """
        # When first time updating the state, create a copy of the original state
        if self._state is self._state_original:
            self._state = deepcopy(self._state_original)
        # Apply the update to the copy of the state
        update.apply(self._state)
        # Add it to the simulation state
        self.all_agents.updates.add(self._state.name, update)
    
    def __getattr__(self, name: str) -> Any:
        try:
            # Make sure the _state attribute is set
            object.__getattribute__(self, '_state')
            # Check if the attribute is in the state
            assert name in self._state.__dataclass_fields__
        except (AttributeError, AssertionError):
            # Keep normal behavior for attributes not in the state
            return object.__getattribute__(self, name)
        
        agent_attr = getattr(self._state, name)
        
        if isinstance(agent_attr, MutableBaseField):
            # If the attribute is a mutable field, return a proxy object mapping to the field
            return MutableFieldProxy(agent_attr, name, self)
        return agent_attr
    
    def __setattr__(self, name: str, value: Any):
        # Keep normal behavior for setting attributes not in the state
        if not hasattr(self, '_state') or name not in self._state.__dataclass_fields__:
            return object.__setattr__(self, name, value)

        # Ignore redundant updates that sets the same value
        if getattr(self._state, name) == value:
            return
        
        self.add_update(AttrUpdate(name, value))
    
    def __repr__(self) -> str:
        return f"Agent({str(self._state.name)})"