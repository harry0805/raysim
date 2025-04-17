from typing import TYPE_CHECKING, Any
from uuid import UUID

from ..mutable_fields.base import MutableBaseField
from ..updating import AgentUpdate, AttrUpdate
from .base_state import AgentState

if TYPE_CHECKING:
    from ..simulation import SimAgents


class Agent:
    """The base class for all agents in the simulation."""
    all_agents: 'SimAgents'
    _state: AgentState
    state: type[AgentState] = AgentState
    
    # Type hint for the type checker, those attributes are actually in AgentState
    name: UUID

    def __init__(self, state: AgentState, all_agents: 'SimAgents'):
        self._state = state
        self.all_agents = all_agents
    
    def register_update(self, update: AgentUpdate):
        """Register a created `AgentUpdate` to the simulation.
        
        This method is intended to only be used internally by the updates tracking system.
        Updates are automatically added when an agent's attribute is modified.
        """
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
        
        value = getattr(self._state, name)
        
        if isinstance(value, MutableBaseField):
            # If the attribute is a mutable field, create a copy and set the context
            value_copy = value.copy()
            value_copy.set_context(name, self)
            # Set this attribute on the Agent instance to so any further access will be the same object
            # Using object.__setattr__ to avoid triggering the __setattr__ method which could potentially add an update
            object.__setattr__(self, name, value_copy)
            return value_copy
        return value
    
    def __setattr__(self, name: str, value: Any):
        """All attributes set on the agent will not be set directly to the state.
        Instead, they will be set on the `Agent` instance and then registered an update to the simulation state.
        This is to make sure the original state is not modified directly.
        So any changed attributes will be stored inside the `Agent` instance.
        """
        # Keep the normal behavior for setting attributes for Agent
        object.__setattr__(self, name, value)

        # When setting an attribute that's included in the state, and if it is changed,
        # Register this update to the simulation state
        if name in self._state.__dataclass_fields__ and getattr(self._state, name) != value:
            if self.all_agents.agent_turn != self._state.name:
                raise RuntimeError(
                    f"Modifying other agent's state is not allowed when it is not that agent's turn."
                )
            self.register_update(AttrUpdate(name, value))
    
    def __repr__(self) -> str:
        return f"Agent({str(self._state.name)})"
    
    def remove_agent(self):
        """Remove this agent from the simulation.
        
        This method will notify the simulation the current agent is to be removed in the next stage.
        """
        self.all_agents.request_remove_agent(self._state.name)
