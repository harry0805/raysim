import random
from raysim import Staging, create_simulation
from raysim.agents import FundsAgent, FundsState


class ExampleAgent(FundsAgent):
    # This attribute doesn't actually belong to this class, but is used to make the type checker happy.
    # The actual attribute is in the ExampleAgentState class.
    funds: int
    
    def random_send(self):
        """Randomly send funds to another agent."""
        targets = random.choices(self.all_agents[ExampleAgent], k=1)
        # Transfer 5% of our funds plus 10 to each target
        amount = self.funds // 20 + 10
        for agent in targets:
            # If we don't have enough funds, send all we have
            if self.funds < amount:
                amount = self.funds
            self.transfer_funds_to(agent, amount)


# starting = [random.randint(1000, 2000) for _ in range(10)]
starting = [1000 for _ in range(100)]
print(starting)
print('total:', sum(starting))

# Specify the staging pattern for the simulation
staging = Staging().add((ExampleAgent, ExampleAgent.random_send))

def main():
    # Construct the initial state of the simulation and create the simulation object
    sim = create_simulation((ExampleAgent.state(funds=f) for f in starting), staging=staging)
    for step, state in enumerate(sim.step(100)):
        # print(f"--------------Step {step + 1}--------------")
        agents = state[ExampleAgent.state]
        
        print(f"Total Funds at step {step + 1}: {sum(agent.funds for agent in agents)}")

        # Calculate the Gini coefficient
        funds = [agent.funds for agent in agents]
        funds.sort()
        n = len(funds)
        cumulative = sum((i + 1) * fund for i, fund in enumerate(funds))
        gini = (2 * cumulative) / (n * sum(funds)) - (n + 1) / n
        print(f"Gini Coefficient at step {step + 1}: {gini:.4f}")

if __name__ == "__main__":
    main()