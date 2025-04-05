import unittest
import uuid
from dataclasses import dataclass, field

# Assuming new locations
from raysim.simulation import SimStateManager, SimAgents
from raysim.agents import AgentState, Agent
from raysim.mutable_fields import AgentSet
from raysim.updating import AgentAddUpdate, AgentRemoveUpdate

# --- Test Setup ---
# Import or define TestAgentState and TestAgent
try:
    # Attempt to import from test_agents if it's structured as a module/package
    from .test_agents import TestAgentState, TestAgent
except ImportError:
    # Define locally if import fails (adjust based on your test structure)
    class TestAgentState(AgentState):
        agents: AgentSet = field(default_factory=AgentSet)
        value: int = 0
        @staticmethod
        def agent():
            return TestAgent
    class TestAgent(Agent):
        value: int
        agents: AgentSet

# --- Test Classes ---

class TestSimStateManagerClass(unittest.TestCase):
    def setUp(self):
        self.agent_state1 = TestAgentState(value=1)
        self.agent_state2 = TestAgentState(value=2)
        self.sim_state_manager = SimStateManager([self.agent_state1])

    def test_initialization(self):
        self.assertIn(TestAgentState, self.sim_state_manager)
        self.assertEqual(len(self.sim_state_manager[TestAgentState]), 1)
        self.assertEqual(len(self.sim_state_manager.all), 1)
        self.assertEqual(self.sim_state_manager.agent_class_map[self.agent_state1.name], TestAgent)

    def test_add_agent(self):
        self.sim_state_manager.add(self.agent_state2)
        self.assertIn(self.agent_state2, self.sim_state_manager[TestAgentState])
        self.assertEqual(len(self.sim_state_manager.all), 2)
        self.assertIn(self.agent_state2.name, self.sim_state_manager.agent_class_map)


    def test_add_multiple_agents(self):
        agent_state3 = TestAgentState(value=3)
        self.sim_state_manager.add([self.agent_state2, agent_state3])
        self.assertEqual(len(self.sim_state_manager[TestAgentState]), 3)
        self.assertEqual(len(self.sim_state_manager.all), 3)
        self.assertIn(agent_state3.name, self.sim_state_manager.agent_class_map)


    def test_remove_agent(self):
        name_to_remove = self.agent_state1.name
        self.sim_state_manager.remove(self.agent_state1)
        # Use get for safer access after removal
        self.assertEqual(len(self.sim_state_manager.get(TestAgentState, {})), 0)
        self.assertEqual(len(self.sim_state_manager.all), 0)
        self.assertNotIn(name_to_remove, self.sim_state_manager.agent_class_map)


    def test_remove_multiple_agents(self):
        self.sim_state_manager.add(self.agent_state2)
        names_to_remove = [self.agent_state1.name, self.agent_state2.name]
        self.sim_state_manager.remove([self.agent_state1, self.agent_state2])
        self.assertEqual(len(self.sim_state_manager.get(TestAgentState, {})), 0)
        self.assertEqual(len(self.sim_state_manager.all), 0)
        self.assertNotIn(names_to_remove[0], self.sim_state_manager.agent_class_map)
        self.assertNotIn(names_to_remove[1], self.sim_state_manager.agent_class_map)


    def test_by_name(self):
        found_agent = self.sim_state_manager.by_name(self.agent_state1.name)
        self.assertEqual(found_agent, self.agent_state1)

    def test_duplicate_agent_add(self):
        """Test that adding duplicate agents raises ValueError"""
        with self.assertRaises(ValueError):
            self.sim_state_manager.add(self.agent_state1)

    def test_remove_nonexistent_agent(self):
        """Test that removing non-existent agent raises ValueError"""
        nonexistent_agent = TestAgentState(value=999)
        with self.assertRaises(ValueError):
            self.sim_state_manager.remove(nonexistent_agent)

    def test_by_name_nonexistent(self):
        """Test that getting non-existent agent by name raises ValueError"""
        with self.assertRaises(ValueError):
            self.sim_state_manager.by_name(uuid.uuid4())

    def test_to_agents_creation(self):
        """Test if SimAgents is created correctly"""
        self.sim_state_manager.add(self.agent_state2)
        sim_agents = self.sim_state_manager.to_agents()
        self.assertIsInstance(sim_agents, SimAgents)
        self.assertEqual(len(sim_agents.all), 2)
        # Check if agents inside are of the correct type
        agent1_instance = sim_agents.by_name(self.agent_state1.name)
        self.assertIsInstance(agent1_instance, TestAgent)
        self.assertEqual(agent1_instance.name, self.agent_state1.name)

    # Test apply_updates is implicitly tested in test_integration.py

class TestSimAgentsClass(unittest.TestCase):
    def setUp(self):
        self.agent_state1 = TestAgentState(value=1)
        self.agent_state2 = TestAgentState(value=2)
        self.sim_state_manager = SimStateManager([self.agent_state1, self.agent_state2])
        self.sim_agents = self.sim_state_manager.to_agents()
        # Retrieve agent instances from SimAgents for convenience
        self.agent1 = self.sim_agents.by_name(self.agent_state1.name)
        self.agent2 = self.sim_agents.by_name(self.agent_state2.name)

    def test_initialization_and_lookup(self):
        self.assertIn(TestAgent, self.sim_agents)
        self.assertEqual(len(self.sim_agents[TestAgent]), 2)
        self.assertEqual(len(self.sim_agents.all), 2)
        self.assertEqual(self.sim_agents.by_name(self.agent1.name), self.agent1)

    def test_by_name_nonexistent(self):
        """Test that getting non-existent agent by name raises ValueError"""
        with self.assertRaises(ValueError):
            self.sim_agents.by_name(uuid.uuid4())

    def test_request_create_agent(self):
        new_agent_state = TestAgentState(value=3)
        self.sim_agents.request_create_agent(new_agent_state)
        # Check updates stored within SimAgents
        self.assertEqual(len(self.sim_agents.updates.sim_updates), 1)
        update = self.sim_agents.updates.sim_updates[0]
        self.assertIsInstance(update, AgentAddUpdate)
        self.assertEqual(update.agent, new_agent_state)

    def test_request_remove_agent(self):
        self.sim_agents.request_remove_agent(self.agent1)
        self.assertEqual(len(self.sim_agents.updates.sim_updates), 1)
        update = self.sim_agents.updates.sim_updates[0]
        self.assertIsInstance(update, AgentRemoveUpdate)
        self.assertEqual(update.agent_name, self.agent1.name)

if __name__ == '__main__':
    unittest.main() 