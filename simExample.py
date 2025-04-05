from dataclasses import dataclass
import random

from raysim import Agent, AgentState


class ExampleAgentState(AgentState):
    @staticmethod
    def agent():
        return ExampleAgent
    funds: int


class ExampleAgent(Agent):
    # This attribute doesn't actually belong to this class, but is used to make the type checker happy.
    # The actual attribute is in the ExampleAgentState class.
    funds: int
    
    def random_send(self):
        """Randomly send funds to another agent."""
        targets = random.choices(self.all_agents[ExampleAgent], k=3)
        # Transfer 5% of our funds to each target
        amount = self.funds // 5
        for agent in targets:
            self.funds -= amount
            agent.funds += amount
