from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from ..agents import Agent, AgentState

type AgentReference = UUID | AgentState | Agent

def agent_ref(agent: AgentReference) -> UUID:
    """Get the name of an agent reference."""
    from ..agents import AgentState, Agent
    if isinstance(agent, UUID):
        return agent
    elif isinstance(agent, (AgentState, Agent)):
        return agent.name
    else:
        raise ValueError(f"Invalid agent reference: {agent.__class__.__name__}")