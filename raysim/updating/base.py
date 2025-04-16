from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterable, Self, Sequence

if TYPE_CHECKING:
    from ..agents.base_state import AgentState
    from ..simulation import SimState


class Update(ABC):
    """A class to store state updates.
    Use this only for type checking.
    
    Attributes:
        priority: The priority of the update. Lower values are applied first.
    """
    priority: int = 0
    
    @abstractmethod
    def apply(self, sim_state: 'AgentState | SimState'):
        """Apply this update to the given `SimState` object."""
        pass
    
    @staticmethod
    def squash(updates: Sequence['Update']) -> Sequence['Update']:
        """When multiple updates can be replaced by fewer updates,
        this `staticmethod` can be implemented to combine them.
        This can be used to optimize the updates size.
        
        Example:
            When multiple `AttrUpdate` updates are trying to update the same attribute,
            we can combine them into a single `AttrUpdate` with the final value.
        
        This method will be called with a list of all potentially combinable updates.
        The output should be a new list, containing the updates after squashing.
        Keep all not combinable updates as is.
        
        Overwrite this method to implement the logic for your update if it is applicable.
        Make sure it is a `staticmethod`.
        """
        return updates


class AgentUpdate(Update):
    """An update which modifies an agent's state.
    This is used for modifying agent attributes.
    """
    @abstractmethod
    def apply(self, agent_state: 'AgentState'):
        """Apply this update to the given `AgentState` object."""
        pass

class SimUpdate(Update):
    """An update which modifies the simulation structure.
    Only used for adding/removing agents.
    """
    @abstractmethod
    def apply(self, sim_state: 'SimState'):
        """Apply this update to the given `SimState` object."""
        pass