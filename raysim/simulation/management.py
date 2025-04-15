from typing import Any, Iterable, overload
from uuid import UUID

from ..agents import Agent, AgentState
from ..agents.utils import AgentReference, agent_ref
from ..updating import AgentAddUpdate, AgentRemoveUpdate, Updates


class SimAgents(dict[type[Agent], list[Agent]]):
    """A dictionary-like object to give agents access to all agents in the current simulation.
    
    Every `Agent` object has a reference to this object in the `all_agents` attribute.
    This allows agent to agent interaction and communication.
    """
    _agents_initialized: bool = False
    updates: Updates
    agent_turn: UUID | None = None
    
    def __init__(self):
        super().__init__()
        self.updates = Updates()
    
    def init_agents[TAgent: Agent](self, agents: Iterable[TAgent]):
        """Initialize the object with agents.
        This method should only be used by the `SimState` class.
        """
        if self._agents_initialized:
            raise RuntimeError("Agents already initialized.")
        for agent in agents:
            if type(agent) not in self:
                self[type(agent)] = []
            self[type(agent)].append(agent)
        self._agents_initialized = True
    
    def set_turn(self, agent: AgentReference):
        """Set which ever `Agent` has the turn to act in the simulation.
        Only one `Agent` can have the turn at a time.
        
        The `Agent` that has the turn is the only one that can modify its state.
        Agents can not modify other agents state directly.
        This is to prevent conflicts during state updates.
        """
        self.agent_turn = agent_ref(agent)
    
    def __getitem__[TAgent: Agent](self, key: type[TAgent]) -> list[TAgent]:
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
        The new agent will be created when `SimState` applies the updates.
        """
        self.updates.add_sim_update(AgentAddUpdate(agent))
    
    def request_remove_agent(self, agent: AgentReference):
        """Request to remove an agent from the simulation.
        This agent will be removed when `SimState` applies the updates.
        """
        self.updates.add_sim_update(AgentRemoveUpdate(agent_ref(agent)))


class SimState(dict[type[AgentState], list[AgentState]]):
    """A dictionary like object to manage and apply updates to the simulation state."""
    step: int = 0
    stage: int | None = None
    state_to_agent: dict[type[AgentState], type[Agent]]

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
        
        self.state_to_agent = {}

    
    @overload
    def __getitem__[TState: AgentState](self, key: type[TState]) -> list[TState]: ...
    @overload
    def __getitem__(self, key: type[Agent]) -> list[Any]: ...
    
    def __getitem__[TState: AgentState](self, key: type[TState] | type[Agent]) -> list[TState]:
        if issubclass(key, Agent):
            key = key.state  # type: ignore
        try:
            return super().__getitem__(key)  # type: ignore
        except KeyError:
            raise KeyError(f"State type '{key.__name__}' not found in the simulation")

    def __repr__(self) -> str:
        items_str = ", ".join(f"{key.__name__}: {value}" for key, value in self.items())
        return f"{{{items_str}}}"

    @property
    def all(self) -> list[AgentState]:
        """Return a list of all agents in the simulation."""
        return [agent for agent_list in self.values() for agent in agent_list]

    def register_agent_to_state(self, pairs: dict[type[AgentState], type[Agent]]):
        """Register each agent state with its corresponding agent class."""
        self.state_to_agent.update(pairs)
    
    def to_agents(self) -> SimAgents:
        """Create a `SimAgents` object with current state of in the simulation."""
        # Check if all agent states are registered with their agent classes
        registered = set(self.state_to_agent.keys())
        existing = set(self.keys())
        if not existing.issubset(registered):
            missing = existing - registered
            raise ValueError(f"Not all AgentStates are registered with their Agent classes. Missing: {tuple(missing)}")
        
        # Create a `SimAgents` object with the current state of the simulation
        sim_agents = SimAgents()
        agents = [self.state_to_agent[type(state)](state, sim_agents) for state in self.all]
        sim_agents.init_agents(agents)
        return sim_agents
    
    def get_names(self, agent_type: type[AgentState] | None = None) -> list[UUID]:
        """Get the names of all agents in the simulation.
        
        Args:
            agent_type: The type of agent to get names for. If None, get names for all agents.
        
        Returns:
            A list of UUIDs representing the names of the agents.
        """
        agents = self.get(agent_type, self.all)  # type: ignore
        return [a.name for a in agents]

    def by_name(self, agent_name: UUID) -> AgentState:
        """Get the agent with a given name in the simulation."""
        try:
            return next(agent for agent in self.all if agent.name == agent_name)
        except StopIteration:
            raise ValueError(f"Could not find agent with ID: {agent_name}")

    def add[TState: AgentState](self, agent: TState | Iterable[TState]):
        """Add a single agent or multiple agents to the simulation."""
        if isinstance(agent, AgentState):
            agent = [agent]

        for a in agent:
            agent_list = self.get(type(a), [])
            if a in agent_list:
                raise ValueError(f"Agent {a} already in the simulation")
            agent_list.append(a)
            self[type(a)] = agent_list

    def remove[TState: AgentState](self, agent: TState | Iterable[TState]):
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
    
    # def to_json(self) -> dict[str, list[dict[str, Any]]]:
    #     json_data = {}
    #     for agent_type, agents in self.items():
    #         json_data[agent_type.__name__] = 
    #         for agent in agents:
