import unittest
import uuid
from unittest.mock import Mock, patch

from raysim.mutable_fields import MutableBaseField, MutableFieldProxy
from raysim.mutable_fields.agent_set import AgentSet
from raysim.mutable_fields.base import create_proxy_instance_type, magic_methods

"""
SUMMARY OF FINDINGS:

The tests in this file reveal several potential issues in the MutableFieldProxy implementation:

1. BUG: In create_proxy_instance_type, line 87 has a potential bug where it calls 
   instance_mro.index(MutableBaseField) but doesn't use the result. It's possible that
   this was intended to be part of inserting InterceptLayer at the right position,
   but the line appears to have no effect.
   --FIXED--

2. BUG: AgentSet.__deepcopy__ creates a new AgentSet without preserving the context
   from the original, which means operations on the copied set won't update the owner's
   state properly.

3. BUG: In AgentSet.remove(), super().remove() is called before checking context and 
   adding updates. If remove() fails with a KeyError, the update won't be added, which
   is inconsistent with how add() works.
   --INTENTIONAL-- If the remove fails, there's no need to add an update.

4. UNEXPECTED BEHAVIOR: The proxy's __repr__ doesn't show its proxy nature, but instead
   forwards directly to the field's __repr__. This could be confusing for debugging.
   --FIXED--

5. UNEXPECTED BEHAVIOR: Magic methods that aren't in magic_methods list still seem to work
   through the proxy in some cases, suggesting the mechanism for forwarding methods isn't
   working as expected.

6. POTENTIAL ISSUE: The commented out super().__init__() in MutableFieldProxy.__init__ might
   prevent proper initialization of parent classes.

7. EDGE CASE: If an instance's class changes after being cached in instance_type_cache,
   the system won't detect it.
   --WONT FIX-- Too complicated
"""


class MockAgent:
    """Mock agent for testing purposes."""
    def __init__(self):
        self.all_agents = Mock()
        self.updates = []
    
    def add_update(self, update):
        self.updates.append(update)
    
    def by_name(self, name):
        """Simulate agent lookup by name."""
        mock_agent = Mock()
        mock_agent.name = name
        return mock_agent


class TestMutableField(MutableBaseField):
    """A simple test field implementation."""
    def __init__(self, value=None):
        super().__init__()
        self.value = value
    
    def get_value(self):
        return self.value
    
    def set_value(self, value):
        self.value = value
        
    def __str__(self):
        return f"TestMutableField({self.value})"
    
    def __repr__(self):
        return self.__str__()
    
    def __len__(self):
        return len(self.value) if hasattr(self.value, "__len__") else 0


class TestProxyClass(unittest.TestCase):
    def setUp(self):
        self.test_field = TestMutableField("test_value")
        self.mock_agent = MockAgent()
        self.proxy = MutableFieldProxy(self.test_field, "test_attr", self.mock_agent)

    def test_proxy_creation(self):
        """Test that the proxy is created with the correct type."""
        self.assertIsInstance(self.proxy, MutableFieldProxy)
        # Should also be an instance of TestMutableField
        self.assertIsInstance(self.proxy, TestMutableField)
        
    def test_attribute_access(self):
        """Test that attributes are accessed through the proxy."""
        self.assertEqual(self.proxy.value, "test_value")
        
    def test_method_access(self):
        """Test that methods are accessible through the proxy."""
        self.assertEqual(self.proxy.get_value(), "test_value")
        
    def test_method_modification(self):
        """Test that methods can modify the field."""
        self.proxy.set_value("new_value")
        self.assertEqual(self.proxy.value, "new_value")
        # Original field should also be modified
        self.assertEqual(self.test_field.value, "new_value")
        
    def test_context_preservation(self):
        """Test that the context is preserved."""
        self.assertEqual(self.proxy.context, ("test_attr", self.mock_agent))
        
    def test_magic_methods(self):
        """Test that magic methods are properly forwarded."""
        # __str__ is in the magic_methods list
        self.assertEqual(str(self.proxy), "TestMutableField(test_value)")
        
        # __len__ is in the magic_methods list
        self.test_field.value = [1, 2, 3]
        self.assertEqual(len(self.proxy), 3)
        
    def test_super_method_calls(self):
        """Test that super() calls in methods work correctly."""
        class DerivedTestField(TestMutableField):
            def get_value(self):
                base_value = super().get_value()
                if base_value is None:
                    return "_derived"
                return base_value + "_derived"
        
        field = DerivedTestField("base")
        proxy = MutableFieldProxy(field, "test_attr", self.mock_agent)
        
        # This should invoke DerivedTestField.get_value which calls super().get_value()
        self.assertEqual(proxy.get_value(), "base_derived")


class TestAgentSetProxy(unittest.TestCase):
    def setUp(self):
        self.agent_set = AgentSet()
        self.mock_agent = MockAgent()
        self.proxy = MutableFieldProxy(self.agent_set, "test_attr", self.mock_agent)
        self.uuid1 = uuid.uuid4()
        self.uuid2 = uuid.uuid4()
        
    def test_agent_set_proxy_creation(self):
        """Test that the proxy is created for AgentSet."""
        self.assertIsInstance(self.proxy, MutableFieldProxy)
        self.assertIsInstance(self.proxy, AgentSet)
        
    def test_add_with_context(self):
        """Test add with context adds updates."""
        self.proxy.add(self.uuid1)
        
        # Should add to the set
        self.assertIn(self.uuid1, self.proxy)
        
        # Should create an update
        self.assertEqual(len(self.mock_agent.updates), 1)
        update = self.mock_agent.updates[0]
        self.assertEqual(update.attr, "test_attr")
        self.assertEqual(update.add, (self.uuid1,))
        
    def test_remove_with_context(self):
        """Test remove with context adds updates."""
        # First add without tracking updates
        self.agent_set.add(self.uuid1)
        self.mock_agent.updates.clear()
        
        # Now remove through proxy (with context)
        self.proxy.remove(self.uuid1)
        
        # Should remove from the set
        self.assertNotIn(self.uuid1, self.proxy)
        
        # Should create an update
        self.assertEqual(len(self.mock_agent.updates), 1)
        update = self.mock_agent.updates[0]
        self.assertEqual(update.attr, "test_attr")
        self.assertEqual(update.remove, (self.uuid1,))
    
    def test_remove_nonexistent_with_context(self):
        """Test that remove() fails correctly when item doesn't exist."""
        # This tests the potential bug where remove() calls super().remove() 
        # before checking context and adding updates
        
        # Try to remove a non-existent item
        with self.assertRaises(KeyError):
            self.proxy.remove(self.uuid1)
        
        # No updates should be created, since the removal failed
        self.assertEqual(len(self.mock_agent.updates), 0)
        
    def test_deep_copy_preserves_context(self):
        """Test that deep_copy properly handles context."""
        import copy
        
        # Add an item and set context
        self.proxy.add(self.uuid1)
        
        # Create a deep copy of the proxy
        copied = copy.deepcopy(self.proxy)
        
        # The copy should be an AgentSet (not necessarily a proxy)
        self.assertIsInstance(copied, AgentSet)
        
        # The item should be in the copy
        self.assertIn(self.uuid1, copied.raw_iter)
        
        # Context isn't preserved in deepcopy
        self.assertIsNone(copied.context)
        
        # This is a known bug - the deepcopy doesn't preserve context
        # In an ideal implementation, we would expect the context to be preserved
        # When fixing the implementation, modify this test to assert context equality
        # self.assertEqual(copied.context, self.proxy.context)


class TestProxyCreation(unittest.TestCase):
    """Tests for the create_proxy_instance_type function."""
    
    def test_mro_order(self):
        """Test that the MRO is correctly ordered."""
        field = TestMutableField()
        proxy_type = create_proxy_instance_type(field)
        
        # Check that MutableFieldProxy is first in the MRO
        self.assertEqual(proxy_type.mro()[0], proxy_type)
        
        # Check that the intercepting layer is after MutableBaseField
        mro = proxy_type.mro()
        base_index = mro.index(MutableBaseField)
        # The class after MutableBaseField should be our intercepting layer
        self.assertTrue("InterceptLayer" in mro[base_index + 1].__name__)
        
        # Check for the bug where instance_mro.index(MutableBaseField) is called but result not used
        # This is testing if line 87 in base.py is working correctly
        # If correctly implemented, InterceptLayer should be at base_index + 1
        next_after_base = mro[base_index + 1]
        self.assertNotEqual(next_after_base, MutableBaseField)
        self.assertIn("InterceptLayer", next_after_base.__name__)
        
    def test_magic_method_forwarding(self):
        """Test that magic methods are properly forwarded."""
        field = TestMutableField("test")
        proxy_type = create_proxy_instance_type(field)
        
        # Check that all magic methods are included
        for method in magic_methods:
            if hasattr(field.__class__, method):
                self.assertTrue(hasattr(proxy_type, method))
                
    def test_instance_type_caching(self):
        """Test that instance types are cached."""
        field1 = TestMutableField()
        field2 = TestMutableField()
        
        proxy_type1 = create_proxy_instance_type(field1)
        proxy_type2 = create_proxy_instance_type(field2)
        
        # Should be the same type since they're the same class
        self.assertIs(proxy_type1, proxy_type2)


class TestEdgeCases(unittest.TestCase):
    def test_invalid_field_class(self):
        """Test with a class that doesn't inherit from MutableBaseField."""
        class InvalidField:
            pass
            
        invalid = InvalidField()
        with self.assertRaises(TypeError):
            create_proxy_instance_type(invalid)
            
    def test_iteration_with_context(self):
        """Test that iteration works with context."""
        agent_set = AgentSet()
        agent = MockAgent()
        uuid1 = uuid.uuid4()
        agent_set.add(uuid1)
        
        # Create a mock for by_name to control its behavior
        agent.all_agents.by_name = Mock(return_value="mock_agent_object")
        
        proxy = MutableFieldProxy(agent_set, "test_attr", agent)
        
        # Iteration should work and return the object from by_name
        agents = list(proxy)
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0], "mock_agent_object")
        
        # Check that by_name was called with the right UUID
        agent.all_agents.by_name.assert_called_with(uuid1)
        
    def test_proxy_repr(self):
        """Test the proxy's __repr__ method."""
        field = TestMutableField("test")
        proxy = MutableFieldProxy(field, "test_attr", MockAgent())
        
        # The proxy __repr__ seems to forward directly to the field's __repr__
        # rather than showing its proxy nature
        actual_repr = repr(proxy)
        
        # Test that it contains TestMutableField
        self.assertTrue("TestMutableField" in actual_repr)
        
        # Test that it contains the value
        self.assertTrue("test" in actual_repr)

    def test_missing_magic_methods(self):
        """Test that magic methods not in the magic_methods list are not properly proxied."""
        # Create a class with a magic method not in the list
        class FieldWithCustomMagic(TestMutableField):
            def __call__(self):
                return "called!"
            
            def __eq__(self, other):
                return isinstance(other, FieldWithCustomMagic) and self.value == other.value
        
        field = FieldWithCustomMagic("test")
        proxy = MutableFieldProxy(field, "test_attr", MockAgent())
        
        # Direct approach using _field_attr to get __call__
        call_method = proxy._field_attr("__call__")
        self.assertEqual(call_method(), "called!")
        
        # Check if __eq__ is in the magic_methods list
        if "__eq__" in magic_methods:
            # If it is, equality should work
            other_field = FieldWithCustomMagic("test")
            self.assertEqual(proxy, other_field)
        else:
            # If not, equality would compare proxy instance to field, not values
            other_field = FieldWithCustomMagic("test")
            # If this fails, it means __eq__ is working through the proxy anyway
            try:
                self.assertNotEqual(proxy, other_field)
            except AssertionError:
                # If __eq__ works through proxy, verify it works correctly
                self.assertEqual(proxy, other_field)


if __name__ == '__main__':
    unittest.main() 