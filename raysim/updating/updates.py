from bisect import bisect_right
from collections import defaultdict
from typing import TYPE_CHECKING, Iterable
from uuid import UUID

from .base import Update, SimUpdate, AgentUpdate

if TYPE_CHECKING:
    from ..simulation import SimState


def optimize_updates_list[UType: Update](updates: Iterable[UType]) -> list[UType]:
    """Remove or combine updates if able based on the
    `Update.squash()` method for each update type.
    """
    # Organize updates by their types in a dictionary
    org_updates = defaultdict[type[UType], list[UType]](list)
    for update in updates:
        org_updates[type(update)].append(update)
    
    # Loop through each update type based on their priority set in that class
    for u_type in sorted(org_updates.keys(), key=lambda u: u.priority):
        # Apply the squash method for that update type
        org_updates[u_type] = u_type.squash(org_updates[u_type])
    
    # Return the flattened updates in a single list
    return [update for updates in org_updates.values() for update in updates]


type USimList = list[SimUpdate]
type UAgentsStore = defaultdict[UUID, list[AgentUpdate]]

class Updates:
    """An object to store updates for the simulation.
    
    Attributes:
        sim_updates: Updates that changes the simulation structure; stored as a `list`.
        agent_updates: Updates that change an agent's state; stored as a `dict` with the agent name as the key.
    """
    def __init__(self):
        super().__init__()
        self.sim_updates: USimList = []
        self.agent_updates: UAgentsStore = defaultdict(list)

    def add(self, agent_name: UUID, update: AgentUpdate):
        """Add an agent update to the simulation which modifies an `AgentState`."""
        self.agent_updates[agent_name].append(update)
    
    def add_sim_update(self, update: SimUpdate):
        """Add a simulation update to the simulation which modifies the simulation structure."""
        self.sim_updates.append(update)
    
    def optimize(self):
        """Remove all redundant updates.
        Remove or combine updates if able based on the `Update.squash()` method.
        """
        self.sim_updates = optimize_updates_list(self.sim_updates)
        self.agent_updates = defaultdict(list, {agent: optimize_updates_list(updates) for agent, updates in self.agent_updates.items()})


def apply_all_updates(sim_state: 'SimState', all_updates: Iterable[Updates]):
    """Apply all updates to the simulation state."""
    # TODO: This function could be optimized further
    
    # Collect all updates from all Updates objects
    sim_updates: list[SimUpdate] = []
    agent_updates_list: list[tuple[UUID, AgentUpdate]] = []
    
    for updates in all_updates:
        # Add simulation updates
        sim_updates.extend(updates.sim_updates)
        
        # Add agent updates with their associated agent ID
        for agent_name, agent_update_list in updates.agent_updates.items():
            for agent_update in agent_update_list:
                agent_updates_list.append((agent_name, agent_update))
    
    # Sort updates by priority (lowest to highest)
    sim_updates.sort(key=lambda update: update.priority)
    agent_updates_list.sort(key=lambda pair: pair[1].priority)
    
    # Apply agent updates
    for agent_name, update in agent_updates_list:
        update.apply(sim_state.by_name(agent_name))
    
    # Apply simulation updates
    for update in sim_updates:
        update.apply(sim_state)
