from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterable, Self

if TYPE_CHECKING:
    from ..agents.base_state import AgentState
    from ..simulation import SimStateManager


class Update(ABC):
    """A class to store state updates.
    Use this only for type checking.
    """
    @abstractmethod
    def apply(self, sim_state: 'AgentState | SimStateManager'):
        """Apply this update to the given `SimStateManager` object."""
        pass
    
    def replacement(self, updates: Iterable[Self]) -> None | tuple[int, Self]:
        """Check if this update can replace or combine with an existing update.
        This can be used to optimize the updates size by replacing or combining updates.
        
        Returns the index of the original update and the new update, or `None` if it fails to find one.
        
        Overwrite this method to implement the logic for your update if it is applicable.
        """
        return None


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
    def apply(self, sim_state: 'SimStateManager'):
        """Apply this update to the given `SimStateManager` object."""
        pass