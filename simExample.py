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
starting = [1000 for _ in range(3)]
print(starting)
print('total:', sum(starting))

# Specify the staging pattern for the simulation
staging = Staging().add((ExampleAgent, ExampleAgent.random_send))


def main():
    # Construct the initial state of the simulation and create the simulation object
    sim = create_simulation((ExampleAgent.state(funds=f) for f in starting), staging=staging)
    sim.run(3)
    print('Complete!')
    
    agents = sim.sim_state[ExampleAgent.state]
    print('Final funds:')
    for agent in agents:
        print(f"{agent.name}: {agent.funds}")

if __name__ == "__main__":
    main()