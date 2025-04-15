import unittest
import uuid
from dataclasses import dataclass, field
from typing import ClassVar # Import ClassVar

# Assuming these are the new locations
from raysim.agents import AgentState, Agent
from raysim.mutable_fields import AgentSet
from raysim.simulation import SimAgents # Needed for Agent init


# --- Test Setup Classes (Commonly used across test files) ---

class TestAgentState(AgentState):
    """Test agent state class"""
    agents: AgentSet = field(default_factory=AgentSet)
    value: int = 0

    @staticmethod
    def agent(): # Add static method
        return TestAgent

class TestAgent(Agent): # Remove generic type hint
    """Test agent class"""
    # Add type hints mirroring TestAgentState for type checker
    agents: AgentSet
    value: int

# --- Test Classes ---

class TestAgentStateClass(unittest.TestCase):
    def test_agent_state_initialization(self):
        state = TestAgentState() # Remove agent=TestAgent
        self.assertEqual(state.value, 0)
        self.assertIsInstance(state.name, uuid.UUID)
        # The state itself doesn't store the agent class directly anymore
        # self.assertEqual(state.agent, TestAgent) # Remove this check

class TestAgentClass(unittest.TestCase):
    def setUp(self):
        # Minimal setup to instantiate Agent for basic tests
        # Requires a dummy SimAgents context
        self.agent_state = TestAgentState(value=1) # Remove agent=TestAgent
        # In a real scenario, SimAgents would be created by SimState
        # For isolated agent tests, we might need a mock or minimal SimAgents
        class MockSimAgents:
            updates = None # Mock updates if needed for specific tests
            def by_name(self, name): return None # Mock lookup
            def __contains__(self, key): return False
            def __getitem__(self, key): raise KeyError
            all = []
            def get(self, key, default=None): return default # Add get method if needed

        self.sim_agents_context = MockSimAgents()
        # Agent instantiation still takes state and context
        self.agent = TestAgent(self.agent_state, self.sim_agents_context)

    def test_agent_initialization(self):
        self.assertEqual(self.agent.name, self.agent_state.name)
        # Test automatic attribute access
        self.assertEqual(self.agent.value, 1)
        self.assertIsInstance(self.agent.agents, AgentSet)

    def test_invalid_attribute_access(self):
        """Test accessing non-existent attribute raises AttributeError"""
        with self.assertRaises(AttributeError):
            _ = self.agent.nonexistent_attr

    def test_setting_readonly_attribute(self):
        """Test setting read-only attributes like name raises AttributeError"""
        with self.assertRaises(AttributeError):
            self.agent.name = uuid.uuid4()

if __name__ == '__main__':
    unittest.main() 