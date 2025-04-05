from uuid import UUID

from .base import SimUpdate, AgentUpdate


class Updates:
    """A dictionary to store updates for each agent.
    Automatically merges updates if they are replaceable based on the `replacement()` method.
    
    Attributes:
        sim_updates: Updates that changes the simulation structure; stored as a `list`.
        agent_updates: Updates that change an agent's state; stored as a `dict` with the agent name as the key.
    """
    sim_updates: list[SimUpdate]
    agent_updates: dict[UUID, list[AgentUpdate]]
    
    def __init__(self):
        super().__init__()
        self.sim_updates = []
        self.agent_updates = {}

    def add(self, agent_name: UUID, update: AgentUpdate):
        """Add an agent update to the simulation which modifies an `AgentState`."""
        if agent_name not in self.agent_updates:
            self.agent_updates[agent_name] = []
        
        target_updates = self.agent_updates[agent_name]
        # If the update is replaceable
        replaceables = (u for u in target_updates if isinstance(u, type(update)))
        if (replacement := update.replacement(replaceables)) is not None:
            # Remove the existing update
            target_updates.pop(replacement[0])
            target_updates.append(replacement[1])
        else:
            target_updates.append(update)
    
    def add_sim_update(self, update: SimUpdate):
        """Add a simulation update to the simulation which modifies the simulation structure."""
        if (replacement := update.replacement(self.sim_updates)) is not None:
            # Remove the existing update
            self.sim_updates.pop(replacement[0])
            self.sim_updates.append(replacement[1])
        else:
            self.sim_updates.append(update)
