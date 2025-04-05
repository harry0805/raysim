import unittest
import uuid
from dataclasses import field

# Import from main raysim package
from raysim import Agent, AgentState, SimStateManager, SimAgents
from raysim.mutable_fields import AgentSet
from raysim.updating import Update, AttrUpdate, AgentAddUpdate, AgentRemoveUpdate, Updates
from raysim.mutable_fields.agent_set import AgentSetUpdate

# --- Test Setup ---
class TestAgentState(AgentState):
    """Test agent state class"""
    agents: AgentSet = field(default_factory=AgentSet)
    value: int = 0
    
    @staticmethod
    def agent():
        return TestAgent

class TestAgent(Agent):
    """Test agent class with attributes mirroring TestAgentState"""
    # Type hints for type checker (these are actually in TestAgentState)
    value: int
    agents: AgentSet

# --- Test Classes ---
class TestBasicInteractionClass(unittest.TestCase):
    """Test basic interactions between Agent and AgentState through SimAgents"""
    
    def setUp(self):
        # Create agent states
        self.agent_state1 = TestAgentState(value=1)
        self.agent_state2 = TestAgentState(value=2)
        
        # Initialize SimStateManager with agent states
        self.sim_state_manager = SimStateManager([self.agent_state1, self.agent_state2])
        
        # Create SimAgents from SimStateManager
        self.sim_agents = self.sim_state_manager.to_agents()
        
        # Get Agent instances from SimAgents
        self.agent1 = self.sim_agents.by_name(self.agent_state1.name)
        self.agent2 = self.sim_agents.by_name(self.agent_state2.name)

    def test_agent_initialization(self):
        """Test if agents are properly initialized with their states"""
        # Check agents were created with correct state values
        self.assertEqual(self.agent1.value, 1)
        self.assertEqual(self.agent2.value, 2)
        
        # Check agent names match their state's names
        self.assertEqual(self.agent1.name, self.agent_state1.name)
        self.assertEqual(self.agent2.name, self.agent_state2.name)
        
        # Check agents have access to SimAgents through all_agents
        self.assertIs(self.agent1.all_agents, self.sim_agents)
        self.assertIs(self.agent2.all_agents, self.sim_agents)

    def test_agent_lookup(self):
        """Test looking up agents by name and type"""
        # Test looking up by name
        self.assertIs(self.sim_agents.by_name(self.agent1.name), self.agent1)
        
        # Test collection access by type
        self.assertIn(self.agent1, self.sim_agents[TestAgent])
        self.assertIn(self.agent2, self.sim_agents[TestAgent])
        self.assertEqual(len(self.sim_agents[TestAgent]), 2)
        
        # Test all agents property
        self.assertEqual(len(self.sim_agents.all), 2)
        self.assertIn(self.agent1, self.sim_agents.all)
        self.assertIn(self.agent2, self.sim_agents.all)
        
        # Test error on non-existent name
        with self.assertRaises(ValueError):
            self.sim_agents.by_name(uuid.uuid4())

class TestUpdateGenerationClass(unittest.TestCase):
    """Test generation and application of updates through agent interaction"""
    
    def setUp(self):
        # Create agent states
        self.agent_state1 = TestAgentState(value=1)
        self.agent_state2 = TestAgentState(value=2)
        
        # Initialize SimStateManager with agent states
        self.sim_state_manager = SimStateManager([self.agent_state1, self.agent_state2])
        
        # Create SimAgents from SimStateManager
        self.sim_agents = self.sim_state_manager.to_agents()
        
        # Get Agent instances from SimAgents
        self.agent1 = self.sim_agents.by_name(self.agent_state1.name)
        self.agent2 = self.sim_agents.by_name(self.agent_state2.name)

    def test_attribute_update_generation(self):
        """Test updating a simple attribute creates the correct update"""
        # Modify attribute through agent
        self.agent1.value = 42
        
        # Check agent local state reflects change immediately
        self.assertEqual(self.agent1.value, 42)
        
        # But original state in manager remains unchanged until updates are applied
        self.assertEqual(self.agent_state1.value, 1)
        
        # Check update is recorded in SimAgents.updates
        self.assertIn(self.agent1.name, self.sim_agents.updates.agent_updates)
        
        updates = self.sim_agents.updates.agent_updates[self.agent1.name]
        self.assertEqual(len(updates), 1)
        
        update = updates[0]
        self.assertIsInstance(update, AttrUpdate)
        self.assertEqual(update.attr, 'value')
        self.assertEqual(update.value, 42)

    def test_redundant_update_not_generated(self):
        """Test that setting a value to its current value generates no update"""
        # Set value to same as current value
        self.agent1.value = 1
        
        # Check no update is generated
        self.assertNotIn(self.agent1.name, self.sim_agents.updates.agent_updates)

    def test_update_replacement(self):
        """Test that consecutive attribute updates replace previous ones"""
        # Set value multiple times
        self.agent1.value = 10
        self.agent1.value = 20
        
        # Check only one update exists
        updates = self.sim_agents.updates.agent_updates[self.agent1.name]
        self.assertEqual(len(updates), 1)
        
        # Check it's the most recent value
        update = updates[0]
        self.assertIsInstance(update, AttrUpdate)
        self.assertEqual(update.value, 20)

class TestAgentSetInteractionClass(unittest.TestCase):
    """Test interactions with AgentSet fields"""
    
    def setUp(self):
        # Create agent states
        self.agent_state1 = TestAgentState(value=1)
        self.agent_state2 = TestAgentState(value=2)
        
        # Initialize SimStateManager with agent states
        self.sim_state_manager = SimStateManager([self.agent_state1, self.agent_state2])
        
        # Create SimAgents from SimStateManager
        self.sim_agents = self.sim_state_manager.to_agents()
        
        # Get Agent instances from SimAgents
        self.agent1 = self.sim_agents.by_name(self.agent_state1.name)
        self.agent2 = self.sim_agents.by_name(self.agent_state2.name)

    def test_agent_set_context(self):
        """Test AgentSet has proper context when accessed through agent"""
        agent_set = self.agent1.agents
        
        # Check context exists
        self.assertTrue(hasattr(agent_set, 'context'))
        context = agent_set.context
        self.assertIsNotNone(context)
        
        # Check context has 2 items (attr name and owner)
        self.assertEqual(len(context), 2)
        attr_name, owner = context
        
        # Verify context contains correct information
        self.assertEqual(attr_name, 'agents')  # First item is attr name
        self.assertIs(owner, self.agent1)  # Second item is owner agent

    def test_agent_set_add_update(self):
        """Test adding to AgentSet creates correct update"""
        # Add agent2 to agent1's set
        self.agent1.agents.add(self.agent2)
        
        # Check agent1's local AgentSet has agent2
        self.assertIn(self.agent2.name, self.agent1.agents.raw_iter)
        
        # But original state doesn't have it yet
        self.assertNotIn(self.agent2.name, self.agent_state1.agents)
        
        # Check update is recorded
        updates = self.sim_agents.updates.agent_updates[self.agent1.name]
        self.assertEqual(len(updates), 1)
        
        update = updates[0]
        self.assertIsInstance(update, AgentSetUpdate)
        self.assertEqual(update.attr, 'agents')
        self.assertEqual(update.add, (self.agent2.name,))
        self.assertEqual(update.remove, ())

    def test_agent_set_remove_update(self):
        """Test removing from AgentSet creates correct update"""
        # First add and apply
        self.agent1.agents.add(self.agent2)
        self.sim_state_manager.apply_updates(self.sim_agents.updates)
        
        # Clear updates
        self.sim_agents.updates = Updates()
        
        # Now remove
        self.agent1.agents.remove(self.agent2)
        
        # Check agent1's local AgentSet no longer has agent2
        self.assertNotIn(self.agent2.name, self.agent1.agents.raw_iter)
        
        # But original state still has it until updates are applied
        self.assertIn(self.agent2.name, self.agent_state1.agents)
        
        # Check update is recorded
        updates = self.sim_agents.updates.agent_updates[self.agent1.name]
        self.assertEqual(len(updates), 1)
        
        update = updates[0]
        self.assertIsInstance(update, AgentSetUpdate)
        self.assertEqual(update.attr, 'agents')
        self.assertEqual(update.add, ())
        self.assertEqual(update.remove, (self.agent2.name,))

    def test_agent_set_iteration(self):
        """Test iterating through AgentSet yields Agent instances"""
        # Add agent2 to agent1's set and apply
        self.agent1.agents.add(self.agent2)
        self.sim_state_manager.apply_updates(self.sim_agents.updates)
        
        # Iterate through set
        agents = list(self.agent1.agents)
        
        # Check we get a single Agent instance
        self.assertEqual(len(agents), 1)
        self.assertIsInstance(agents[0], TestAgent)
        self.assertEqual(agents[0].name, self.agent2.name)

class TestSimUpdateClass(unittest.TestCase):
    """Test simulation-level updates (adding/removing agents)"""
    
    def setUp(self):
        # Create agent states
        self.agent_state1 = TestAgentState(value=1)
        self.agent_state2 = TestAgentState(value=2)
        
        # Initialize SimStateManager with agent states
        self.sim_state_manager = SimStateManager([self.agent_state1, self.agent_state2])
        
        # Create SimAgents from SimStateManager
        self.sim_agents = self.sim_state_manager.to_agents()
        
        # Get Agent instances from SimAgents
        self.agent1 = self.sim_agents.by_name(self.agent_state1.name)
        self.agent2 = self.sim_agents.by_name(self.agent_state2.name)

    def test_request_create_agent(self):
        """Test requesting agent creation generates correct update"""
        # Create new agent state
        new_agent_state = TestAgentState(value=3)
        
        # Request creation
        self.sim_agents.request_create_agent(new_agent_state)
        
        # Check update is recorded
        self.assertEqual(len(self.sim_agents.updates.sim_updates), 1)
        
        update = self.sim_agents.updates.sim_updates[0]
        self.assertIsInstance(update, AgentAddUpdate)
        self.assertIs(update.agent, new_agent_state)
        
        # Apply updates
        self.sim_state_manager.apply_updates(self.sim_agents.updates)
        
        # Check agent is now in the simulation
        self.assertIn(new_agent_state, self.sim_state_manager[TestAgentState])
        self.assertEqual(len(self.sim_state_manager.all), 3)

    def test_request_remove_agent(self):
        """Test requesting agent removal generates correct update"""
        # Request removal
        self.sim_agents.request_remove_agent(self.agent2)
        
        # Check update is recorded
        self.assertEqual(len(self.sim_agents.updates.sim_updates), 1)
        
        update = self.sim_agents.updates.sim_updates[0]
        self.assertIsInstance(update, AgentRemoveUpdate)
        self.assertEqual(update.agent_name, self.agent2.name)
        
        # Apply updates
        self.sim_state_manager.apply_updates(self.sim_agents.updates)
        
        # Check agent is removed from the simulation
        self.assertNotIn(self.agent_state2, self.sim_state_manager[TestAgentState])
        self.assertEqual(len(self.sim_state_manager.all), 1)

class TestComplexUpdateScenarioClass(unittest.TestCase):
    """Test complex scenarios involving multiple types of updates"""
    
    def setUp(self):
        # Create agent states
        self.agent_state1 = TestAgentState(value=1)
        self.agent_state2 = TestAgentState(value=2)
        
        # Initialize SimStateManager with agent states
        self.sim_state_manager = SimStateManager([self.agent_state1, self.agent_state2])
        
        # Create SimAgents from SimStateManager
        self.sim_agents = self.sim_state_manager.to_agents()
        
        # Get Agent instances from SimAgents
        self.agent1 = self.sim_agents.by_name(self.agent_state1.name)
        self.agent2 = self.sim_agents.by_name(self.agent_state2.name)

    def test_multiple_update_types(self):
        """Test multiple different types of updates applied together"""
        # Create a new agent
        new_agent_state = TestAgentState(value=3)
        self.sim_agents.request_create_agent(new_agent_state)
        
        # Modify agent1's attribute
        self.agent1.value = 42
        
        # Add agent2 to agent1's set
        self.agent1.agents.add(self.agent2)
        
        # Request removal of agent2 (will be processed after adding to agent1's set)
        self.sim_agents.request_remove_agent(self.agent2)
        
        # Apply all updates
        self.sim_state_manager.apply_updates(self.sim_agents.updates)
        
        # Check results:
        
        # 1. New agent should be added
        self.assertIn(new_agent_state, self.sim_state_manager[TestAgentState])
        
        # 2. Agent1's value should be updated
        self.assertEqual(self.agent_state1.value, 42)
        
        # 3. Agent2 should be removed
        self.assertNotIn(self.agent_state2, self.sim_state_manager[TestAgentState])
        
        # 4. Agent1's agents set should have agent2's name (even though agent2 is removed)
        self.assertIn(self.agent2.name, self.agent_state1.agents)
        
        # 5. We should have 2 agents total (agent1 and new_agent)
        self.assertEqual(len(self.sim_state_manager.all), 2)

if __name__ == '__main__':
    unittest.main()