from typing import TYPE_CHECKING, Iterable, TypeVar
from uuid import UUID

from ..agents import Agent, AgentState
from ..agents.utils import AgentReference, agent_ref
from ..updating import AgentAddUpdate, AgentRemoveUpdate, Updates


AgentLike = TypeVar('AgentLike', bound=Agent)

class SimAgents(dict[type[Agent], list[Agent]]):
    """A dictionary-like object to give agents access to all agents in the current simulation.
    
    Every `Agent` object has a reference to this object in the `all_agents` attribute.
    This allows agent to agent interaction and communication.
    """
    _agents_initialized: bool = False
    updates: Updates
    
    def __init__(self):
        super().__init__()
        self.updates = Updates()
    
    def init_agents(self, agents: Iterable[AgentLike]):
        """Initialize the object with agents.
        This method should only be used by the `SimStateManager` class.
        """
        if self._agents_initialized:
            raise RuntimeError("Agents already initialized.")
        for agent in agents:
            if type(agent) not in self:
                self[type(agent)] = []
            self[type(agent)].append(agent)
        self._agents_initialized = True
    
    def __getitem__(self, key: type[AgentLike]) -> list[AgentLike]:
        try:
            return super().__getitem__(key)  # type: ignore
        except KeyError:
            raise KeyError(f"Agent type {key.__name__} not found in the simulation")
    
    @property
    def all(self) -> list[Agent]:
        """Return a list of all agent state accessors in the simulation."""
        return [agent for agent_list in self.values() for agent in agent_list]
    
    def by_name(self, agent_name: UUID) -> Agent:
        """Get the agent with a given name in the simulation."""
        try:
            return next(agent for agent in self.all if agent.name == agent_name)
        except StopIteration:
            raise ValueError(f"Could not find agent with ID: {agent_name}")
    
    def request_create_agent(self, agent: AgentState):
        """Request to create a new agent in the simulation.
        The new agent will be created when `SimStateManager` applies the updates.
        """
        self.updates.add_sim_update(AgentAddUpdate(agent))
    
    def request_remove_agent(self, agent: AgentReference):
        """Request to remove an agent from the simulation.
        This agent will be removed when `SimStateManager` applies the updates.
        """
        self.updates.add_sim_update(AgentRemoveUpdate(agent_ref(agent)))


StateType = TypeVar('StateType', bound=AgentState)

class SimStateManager(dict[type[AgentState], list[AgentState]]):
    """A dictionary like object to manage and apply updates to the simulation state."""
    step: int = 0
    stage: str | None = None

    def __init__(self, agent_states: Iterable[AgentState]):
        super().__init__()
        exists = set()
        # Initialize the dictionary with agent states
        for agent in agent_states:
            if type(agent) not in self:
                self[type(agent)] = []
            # Make sure no duplicate agent names are added
            if agent.name in exists:
                continue
            self[type(agent)].append(agent)

    def __getitem__(self, key: type[StateType]) -> list[StateType]:
        try:
            return super().__getitem__(key)  # type: ignore
        except KeyError:
            raise KeyError(f"Agent type {key.__name__} not found in the simulation")

    def __repr__(self) -> str:
        items_str = ", ".join(f"{key.__name__}: {value}" for key, value in self.items())
        return f"{{{items_str}}}"

    @property
    def all(self) -> list[AgentState]:
        """Return a list of all agents in the simulation."""
        return [agent for agent_list in self.values() for agent in agent_list]

    def to_agents(self) -> SimAgents:
        """Create a `SimAgents` object with current state of in the simulation."""
        sim_agents = SimAgents()
        sim_agents.init_agents([state.agent()(state, sim_agents) for state in self.all])
        return sim_agents

    def by_name(self, agent_name: UUID) -> AgentState:
        """Get the agent with a given name in the simulation."""
        try:
            return next(agent for agent in self.all if agent.name == agent_name)
        except StopIteration:
            raise ValueError(f"Could not find agent with ID: {agent_name}")

    def add(self, agent: StateType | Iterable[StateType]):
        """Add a single agent or multiple agents to the simulation."""
        if isinstance(agent, AgentState):
            agent = [agent]

        for a in agent:
            agent_list = self.get(type(a), [])
            if a in agent_list:
                raise ValueError(f"Agent {a} already in the simulation")
            agent_list.append(a)
            self[type(a)] = agent_list

    def remove(self, agent: StateType | Iterable[StateType]):
        """Remove a single agent or multiple agents from the simulation."""
        if isinstance(agent, AgentState):
            agent = [agent]

        for a in agent:
            agent_list = self.get(type(a), [])
            if a not in agent_list:
                raise ValueError(f"Agent {a} not in the simulation")
            agent_list.remove(a)
    
    def apply_updates(self, updates: Updates):
        """Apply updates to the simulation."""
        for agent_name, agent_updates in updates.agent_updates.items():
            agent = self.by_name(agent_name)
            [update.apply(agent) for update in agent_updates]
        
        for update in updates.sim_updates:
            update.apply(self)