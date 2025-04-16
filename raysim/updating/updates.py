from bisect import bisect_right
from typing import TYPE_CHECKING, Iterable, cast
from uuid import UUID

from .base import Update, SimUpdate, AgentUpdate

if TYPE_CHECKING:
    from ..simulation import SimState

class UpdatesList[UType: Update]:
    """A list of updates sorted by priority."""
    def __init__(self):
        self.u_store: list[UType] = []
    
    def add(self, update: UType):
        """Add an update to the list."""
        insertion = bisect_right(self.u_store, update.priority, key=lambda u: u.priority)
        self.u_store.insert(insertion, update)
    
    def priorities(self) -> list[int]:
        """Get the list of priorities in the list."""
        return sorted(set(u.priority for u in self.u_store))
    
    def priority_iter(self) -> Iterable[list[UType]]:
        """Yield updates sorted by priority."""
        for priority in sorted(self.u_store.keys()):
            yield self.u_store[priority]

    def __iter__(self) -> Iterable[UType]:
        """Iterate over all updates in the list."""
        for updates in self.priority_iter():
            yield from updates

    def __getitem__(self, priority: int) -> list[UType]:
        """Get the updates for a given priority."""
        return self.u_store.get(priority, [])
    
    def squash(self):
        """Remove all redundant updates inside this `UpdatesList`."""
        pass


class AgentUpdatesStore(dict[UUID, UpdatesList[AgentUpdate]]):
    """A dictionary to store updates for each agent."""
    def priority_iter(self) -> Iterable[list[AgentUpdate]]:
        """Iterate though all updates by priority."""
        # Get the possible priorities from all updates lists
        priorities = sorted(set(p for u_list in self.values() for p in u_list.priorities()))
        for p in priorities:
            yield [u for u_list in self.values() for u in u_list[p]]
    
    def add(self, agent_name: UUID, update: AgentUpdate):
        """Add an agent update to the simulation which modifies an `AgentState`."""
        if agent_name not in self:
            self[agent_name] = UpdatesList()
        self[agent_name].add(update)
    
    def squash_all(self):
        """Remove all redundant updates."""
        [updates.squash() for updates in self.values()]


class Updates:
    """An object to store updates for the simulation.
    
    Attributes:
        sim_updates: Updates that changes the simulation structure; stored as a `list`.
        agent_updates: Updates that change an agent's state; stored as a `dict` with the agent name as the key.
    """
    def __init__(self):
        super().__init__()
        self.sim_updates = UpdatesList[SimUpdate]()
        self.agent_updates = AgentUpdatesStore()

    def add(self, agent_name: UUID, update: AgentUpdate):
        """Add an agent update to the simulation which modifies an `AgentState`."""
        self.agent_updates.add(agent_name, update)
    
    def add_sim_update(self, update: SimUpdate):
        """Add a simulation update to the simulation which modifies the simulation structure."""
        self.sim_updates.add(update)
    
    def squash(self):
        """Remove all redundant updates.
        Remove or combine updates if able based on the `Update.squash()` method.
        """
        self.sim_updates.squash()
        self.agent_updates.squash_all()


def apply_all_updates(sim_state: 'SimState', updates: Iterable[Updates]):
    """Apply all updates to the simulation state."""
    pass