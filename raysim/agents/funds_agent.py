from ..updating import NumericUpdate
from .base_agent import Agent
from .base_state import AgentState


class FundsState(AgentState):
    funds: int | float


class FundsAgent(Agent):
    state: type[FundsState] = FundsState
    funds: int | float
    
    def transfer_funds_to(self, target: 'FundsAgent', amount: int | float) -> None:
        """Transfer funds to another agent."""
        # Skip redundant transfers
        if amount == 0:
            return
        
        if amount < 0:
            raise ValueError("Sending amount must be positive. Receiving funds is not supported.")
        
        if self.funds < amount:
            raise ValueError("Not enough funds to transfer.")
        
        self.funds -= amount
        # Schedule the update for the target agent
        target.register_update(NumericUpdate(attr='funds', delta=amount))
