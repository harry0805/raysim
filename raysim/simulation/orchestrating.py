from uuid import UUID
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Iterator, Self
from collections import deque

import ray
from tqdm import tqdm

from ..updating import Updates
from ..agents import Agent, AgentState
from .management import SimState


@dataclass
class StageTask[TargetAgent: Agent]:
    """A dataclass for containing what an agent should do in a stage."""
    agent: type[TargetAgent]
    method: Callable[[TargetAgent], Any]
    
    def __post_init__(self):
        # Check if the method is callable
        if not callable(self.method):
            raise TypeError(f"Method {self.method} is not callable.")
        # Check if agent has a valid state type
        if not isinstance(getattr(self.agent, 'state'), type):
            raise AttributeError(f"Agent type {self.agent} did not specify a valid state type.")

type TasksList = list[StageTask[Agent]]
type StagingStack = list[TasksList]

class Staging:
    """A class for containing tasks stages in the simulation.
    All tasks in a single stage are executed in parallel.
    """
    stages: StagingStack

    def __init__(self):
        self.stages = []
    
    def add[TAgent: Agent](self, *args: tuple[type[TAgent], Callable[[TAgent], Any] | str]) -> Self:
        """Add a stage to the simulation."""
        tasks = []
        for agent, method in args:
            if isinstance(method, str):
                # Check if the method is a string and get the method from the agent class
                if not hasattr(agent, method):
                    raise AttributeError(f"'{method}' is not a valid method of '{agent}'.")
                method = getattr(agent, method)
            # Add the StageTask to the list of tasks
            tasks.append(StageTask(agent, method))
        # Append this stage to the staging list
        self.stages.append(tasks)
        return self
    
    def __iter__(self) -> Iterator[TasksList]:
        """Iterate over the stages."""
        return iter(self.stages)

@ray.remote
def task_executor(agent_name: UUID, method_name: str, sim_state: SimState) -> Updates:
    """Execute a task for an agent using a reference to the simulation state.
    
    Args:
        agent_name: UUID of the agent to execute the task on
        method_name: Name of the method to execute
        sim_state_ref: Ray object reference to the simulation state
        
    Returns:
        Updates object containing changes made by the agent
    """
    # Get the simulation state from the Ray object store
    # sim_state: SimState = ray.get(sim_state_ref)
    
    # Get the agent from the simulation state using the agent name
    all_agents = sim_state.to_agents()
    target_agent = all_agents.by_name(agent_name)
    all_agents.set_turn(target_agent.name)
    
    # Execute the method on the target agent
    getattr(target_agent, method_name)()
    
    # Return only the updates instead of the whole state
    return all_agents.updates


class Simulation:
    """A class for running the simulation."""
    def __init__(self, sim_state: SimState, staging: Staging, init_ray=True):
        self.staging = staging
        self.sim_state = sim_state
        if init_ray:
            ray.init()
        self.past_updates = deque[Updates](maxlen=50)
    
    def apply_updates(self, updates: Updates):
        """Apply updates to the simulation state."""
        self.sim_state.apply_updates(updates)
        # TODO: Detect conflicting updates and handle them
        self.past_updates.append(updates)
    
    def execute_stage(self, stage_tasks: TasksList):
        """Run a single stage in the simulation."""
        self.sim_state.register_agent_to_state({task.agent.state: task.agent for task in stage_tasks})
        sim_state_ref = ray.put(self.sim_state)
        # Create a list of tasks to run in parallel
        pending_tasks = []
        for task in stage_tasks:
            tasked_agent_names: list[UUID] = self.sim_state.get_names(task.agent.state)
            for name in tasked_agent_names:
                # Launch remote task with minimal data
                pending_tasks.append(task_executor.remote(name, task.method.__name__, sim_state_ref))
        
        # Use ray.wait to process results as they become available
        while pending_tasks:
            # Get results as they finish without waiting for all to complete
            finished_tasks, pending_tasks = ray.wait(pending_tasks, timeout=0.01)
            if finished_tasks:
                # Process completed tasks immediately
                for update_id in finished_tasks:
                    updates_list = ray.get(update_id)
                    if isinstance(updates_list, Updates):
                        updates_list = [updates_list]
                    [self.apply_updates(u) for u in updates_list]

    def step(self):
        """Run the next step in the simulation."""
        self.sim_state.step += 1
        for idx, stage_tasks in enumerate(self.staging):
            self.sim_state.stage = idx
            self.execute_stage(stage_tasks)
    
    def run(self, steps: int):
        """Run the simulation for a specified number of steps."""
        [self.step() for _ in tqdm(range(steps))]


def create_simulation(states: Iterable[AgentState], staging: Staging) -> Simulation:
    """Create a simulation from a list of states and a staging pattern."""
    sim_state = SimState(states)
    return Simulation(sim_state, staging)