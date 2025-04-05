from dataclasses import dataclass
from typing import Callable, Any, TypeVar, Generic, Optional
from abc import ABC, abstractmethod

import ray

from raysim import (
    Agent,
    AgentState,
    SimStateManager,
    SimAgents,
)


TargetAgent = TypeVar("TargetAgent", bound=Agent)
@dataclass
class Task(Generic[TargetAgent]):
    """A dataclass for containing task information."""
    agent: type[TargetAgent]
    method: Callable[[TargetAgent], Any]


class Staging:
    """A class for containing tasks stages in the simulation.
    All tasks in a single stage are executed in parallel.
    """
    stages: list[list[Task]]

    def __init__(self):
        self.stages = []
    
    def stage(self, tasks: list[Task]):
        """Add a stage to the simulation."""
        self.stages.append(tasks)


class Simulation:
    """A class for running the simulation."""
    def __init__(self, staging: Staging):
        self.staging = staging
        self.sim_state_manager = None

    def initialize(self, initial_agents: list[AgentState]):
        """Initialize the simulation with a set of agents."""
        self.sim_state_manager = SimStateManager(initial_agents)
        
    def run(self):
        """Run the simulation through all stages."""
        if not self.sim_state_manager:
            raise RuntimeError("Simulation not initialized. Call initialize() first.")
        
        for stage_num, stage in enumerate(self.staging.stages):
            self.sim_state_manager.stage = f"Stage {stage_num}"
            self._process_stage(stage)
            self.sim_state_manager.step += 1
            
        self.sim_state_manager.stage = None
        return self.sim_state_manager
    
    def _process_stage(self, stage: list[Task]):
        """Process a single stage of tasks."""
        # Group tasks by agent type for better performance
        tasks_by_agent_type = {}
        for task in stage:
            if task.agent not in tasks_by_agent_type:
                tasks_by_agent_type[task.agent] = []
            tasks_by_agent_type[task.agent].append(task.method)
        
        # Execute tasks for each agent type in parallel
        updates_list = []
        for agent_type, methods in tasks_by_agent_type.items():
            # Create a reference to agents of this type
            if agent_type not in self.sim_state_manager:
                continue
                
            agent_states = self.sim_state_manager[agent_type]
            if not agent_states:
                continue
                
            # Run tasks in parallel using Ray
            updates_list.extend(self._execute_tasks_parallel(agent_type, agent_states, methods))
        
        # Merge all updates
        merged_updates = Updates()
        for updates in updates_list:
            # Merge sim updates
            for update in updates.sim_updates:
                merged_updates.add_sim_update(update)
            
            # Merge agent updates
            for agent_name, agent_updates in updates.agent_updates.items():
                for update in agent_updates:
                    merged_updates.add(agent_name, update)
        
        # Apply all updates at once
        self.sim_state_manager.apply_updates(merged_updates)
    
    def _execute_tasks_parallel(self, agent_type: type[Agent], agent_states: list[AgentState], methods: list[Callable]):
        """Execute tasks for agents of a specific type in parallel."""
        # Create remote tasks
        remote_tasks = []
        
        for agent_state in agent_states:
            remote_tasks.append(_agent_task_executor.remote(
                agent_type, 
                agent_state, 
                methods, 
                self.sim_state_manager.all
            ))
        
        # Wait for all tasks to complete
        return ray.get(remote_tasks)


@ray.remote
def _agent_task_executor(agent_type: type[Agent], agent_state: AgentState, methods: list[Callable], all_agent_states: list[AgentState]):
    """Execute multiple methods on a single agent."""
    # Create a SimStateAccessor for this agent
    sim_state_accessor = SimAgents(all_agent_states)
    agent_accessor = sim_state_accessor.by_name(agent_state.name)
    
    # Create the agent instance
    agent = agent_type(agent_accessor, sim_state_accessor)
    
    # Execute each method on the agent
    for method in methods:
        method(agent)
    
    # Return the updates
    return sim_state_accessor.updates
