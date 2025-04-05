from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Iterator, Optional
from uuid import UUID

from ..agents.utils import AgentReference, agent_ref
from ..updating.base import AgentUpdate
from .base import MutableBaseField

if TYPE_CHECKING:
    from ..agents import Agent, AgentState


class AgentSet(MutableBaseField, set[UUID]):
    """An optimized set that stores agents as its name within a given `simulationAgents` object.
    This class is a supported field type in `AgentState` objects.
    
    Adding and removing agents can be done by an agent reference which is
    either a `UUID` (name), an `AgentState` object, or an `Agent` object.
    
    **Note**: Iterating over agents can only be done when this set is accessed as an attribute
    via an `Agent` object. Iterating over agent names are always available via `raw_iter`.
    """
    def __init__(self, agents: Iterable[AgentReference]=()):
        super().__init__()
        self.update(agents)
    
    def _get_agent(self, agent: UUID) -> 'Agent':
        """Get the agent object from the `simulationAgents` object."""
        if not self.context:
            raise self._context_required_error
        _, owner = self.context
        return owner.all_agents.by_name(agent)

    def __iter__(self) -> Iterator['Agent']:
        """Returns an iterator over agent states."""
        for agent_id in super().__iter__():
            yield self._get_agent(agent_id)
    
    @property
    def raw_iter(self) -> Iterator[UUID]:
        """Returns an iterator over the raw agent names."""
        return super().__iter__()
    
    def __deepcopy__(self, memo):
        """Return a deep copy of the set."""
        new_set = AgentSet()
        for agent in self.raw_iter:
            new_set.add(agent)
        return new_set

    def __contains__(self, agent: Any) -> bool:
        """Check if an agent is in the set."""
        name = agent_ref(agent)
        return super().__contains__(name)
    
    def __repr__(self) -> str:
        try:
            return super().__repr__()
        except RuntimeError:
            return object.__repr__(self)
    
    def add(self, agent: AgentReference):
        """Add an agent to the set."""
        # Return if the agent is already in the set
        if (name := agent_ref(agent)) in self:
            return
        # When given a context, add an update to the owner
        if self.context:
            attr, owner = self.context
            owner.add_update(AgentSetUpdate(attr, add=(name,)))
        super().add(name)
    
    def update(self, agents: Iterable[AgentReference]):
        """Update the set with the union of itself and other agents."""
        [self.add(agent) for agent in agents]
    
    def remove(self, agent: AgentReference):
        """Remove an agent from this set; it must be a member."""
        super().remove(name := agent_ref(agent))
        # When given a context, add an update to the owner
        if self.context:
            attr, owner = self.context
            owner.add_update(AgentSetUpdate(attr, remove=(name,)))

    def discard(self, agent: AgentReference):
        """Remove an agent from the set if it is a member."""
        try:
            self.remove(agent)
        except KeyError:
            pass
    
    def pop(self):
        """Not supported. Use `remove()` or `discard()` instead."""
        raise NotImplementedError("AgentSet does not support pop() operation. Use remove() or discard() instead.")


@dataclass
class AgentSetUpdate(AgentUpdate):
    """Modify an agentSet attribute for a state.

    Attributes:
        attr: The attribute to modify.
        add: The agents to add to the set.
        remove: The agents to remove from the set.
    """
    attr: str
    add: tuple[UUID, ...] = field(default_factory=tuple)
    remove: tuple[UUID, ...] = field(default_factory=tuple)

    def apply(self, context: 'AgentState'):
        """Apply this update to change an `AgentSet` attribute on an
        `AgentState` by adding and/or removing elements.
        """
        # Get the agentSet attribute
        attr: set[UUID] = getattr(context, self.attr)
        # Add the agents to the set
        attr.update(self.add)
        # Remove the agents from the set
        for agent in self.remove:
            attr.discard(agent)
    
    def replacement(self, updates: Iterable['AgentSetUpdate']) -> None | tuple[int, 'AgentSetUpdate']:
        """Check if this update can replace or combine with an existing update."""
        for i, update in enumerate(updates):
            if isinstance(update, AgentSetUpdate) and update.attr == self.attr:
                # Check if the updates are compatible
                new_add = set(self.add) - set(update.remove)
                new_remove = set(self.remove) - set(update.add)
                return i, AgentSetUpdate(self.attr, tuple(new_add), tuple(new_remove))
        return None
