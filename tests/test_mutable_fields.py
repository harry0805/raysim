import unittest
import uuid

from raysim.mutable_fields import AgentSet

# --- Test Class ---
class TestAgentSetClass(unittest.TestCase):
    def setUp(self):
        # Create a contextless AgentSet for testing
        self.agent_set = AgentSet()
        # Store some dummy UUIDs for testing add/remove operations
        self.dummy_uuid1 = uuid.uuid4()
        self.dummy_uuid2 = uuid.uuid4()
        self.dummy_uuid3 = uuid.uuid4()

    def test_initialization(self):
        """Test basic initialization"""
        self.assertEqual(len(self.agent_set), 0)
        # Check internal state if relevant, e.g., raw_iter is empty
        self.assertEqual(list(self.agent_set.raw_iter), [])

    def test_initialization_with_data(self):
        """Test initialization with an iterable of UUIDs"""
        initial_data = {self.dummy_uuid1, self.dummy_uuid2}
        agent_set = AgentSet(initial_data)
        self.assertEqual(len(agent_set), 2)
        self.assertEqual(set(agent_set.raw_iter), initial_data)

    # --- Methods that REQUIRE context ---

    def test_iteration_without_context(self):
        """Test iterating AgentSet without context raises RuntimeError"""
        self.agent_set.add(self.dummy_uuid1)
        with self.assertRaises(RuntimeError):
            next(iter(self.agent_set))  # __iter__ requires context

    # --- Methods that work WITHOUT context (but add updates WITH context) ---

    def test_add_without_context(self):
        """Test add works without context"""
        # Should work without error - add() works without context
        self.agent_set.add(self.dummy_uuid1)
        self.assertIn(self.dummy_uuid1, self.agent_set)
        self.assertEqual(len(self.agent_set), 1)

    def test_update_without_context(self):
        """Test update works without context"""
        # Should work without error - update() works without context
        self.agent_set.update([self.dummy_uuid1, self.dummy_uuid2])
        self.assertIn(self.dummy_uuid1, self.agent_set)
        self.assertIn(self.dummy_uuid2, self.agent_set)
        self.assertEqual(len(self.agent_set), 2)

    def test_remove_without_context(self):
        """Test remove works without context"""
        self.agent_set.add(self.dummy_uuid1)
        # Should work without error - remove() works without context
        self.agent_set.remove(self.dummy_uuid1)
        self.assertNotIn(self.dummy_uuid1, self.agent_set)
        self.assertEqual(len(self.agent_set), 0)

    def test_discard_without_context(self):
        """Test discard works without context"""
        self.agent_set.add(self.dummy_uuid1)
        # Should work without error - discard() works without context
        self.agent_set.discard(self.dummy_uuid1)
        self.assertNotIn(self.dummy_uuid1, self.agent_set)
        self.assertEqual(len(self.agent_set), 0)
        
        # Discard non-existent should also work
        self.agent_set.discard(self.dummy_uuid2)  # No error

    def test_contains_without_context(self):
        """Test __contains__ works without context"""
        self.agent_set.add(self.dummy_uuid1)
        # Should work without error - __contains__ doesn't require context
        self.assertTrue(self.dummy_uuid1 in self.agent_set)
        self.assertFalse(self.dummy_uuid2 in self.agent_set)

    # --- Basic functionality tests ---

    def test_remove_nonexistent(self):
        """Test remove raises KeyError for non-existent item"""
        with self.assertRaises(KeyError):
            self.agent_set.remove(self.dummy_uuid1)

    def test_add_duplicate(self):
        """Test adding duplicate doesn't add twice"""
        self.agent_set.add(self.dummy_uuid1)
        initial_size = len(self.agent_set)
        self.agent_set.add(self.dummy_uuid1)  # Add again
        self.assertEqual(len(self.agent_set), initial_size)  # Size shouldn't change

    def test_raw_iteration(self):
        """Test raw_iter property for iterating names"""
        self.agent_set.add(self.dummy_uuid1)
        self.agent_set.add(self.dummy_uuid2)
        raw_names = set(self.agent_set.raw_iter)
        self.assertEqual(raw_names, {self.dummy_uuid1, self.dummy_uuid2})

    def test_pop_not_supported(self):
        """Test that pop operation raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.agent_set.pop()

if __name__ == '__main__':
    unittest.main() 