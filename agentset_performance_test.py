#!/usr/bin/env python
"""
Performance comparison between direct AgentSet usage and proxied AgentSet.

This script compares the performance overhead of using a proxied AgentSet via MutableFieldProxy
versus using a raw AgentSet directly.
"""
import timeit
import uuid
from dataclasses import field
from typing import List, Optional, Tuple
import sys
import gc

from raysim.agents import Agent, AgentState
from raysim.mutable_fields import AgentSet
from raysim.mutable_fields.base import MutableBaseField, MutableFieldProxy
from raysim.updating import Updates

# Create a simple TestAgentState and TestAgent class for testing
class TestAgentState(AgentState):
    """Test agent state for performance testing."""
    agents: AgentSet = field(default_factory=AgentSet)
    value: int = 0

    @staticmethod
    def agent():
        return TestAgent

class TestAgent(Agent):
    """Test agent for performance testing."""
    # Type hints for type checker
    agents: AgentSet
    value: int

# Mock SimAgents class with minimal implementation for testing
class MockSimAgents:
    """Minimal SimAgents implementation for testing."""
    def __init__(self):
        self.updates = Updates()
        self._agents = {}
    
    def by_name(self, name):
        """Mock lookup method."""
        return self._agents.get(name)
    
    def __contains__(self, key):
        return key in self._agents
    
    def __getitem__(self, key):
        return self._agents.get(key, [])
    
    @property
    def all(self):
        return list(self._agents.values())

def create_proxy_for_test(agent_set: AgentSet, owner_agent: Agent, attr_name: str = "agents") -> AgentSet:
    """Create a proxied AgentSet for testing."""
    return MutableFieldProxy(agent_set, attr_name, owner_agent)

def generate_uuids(count: int) -> List[uuid.UUID]:
    """Generate a list of UUIDs for testing."""
    return [uuid.uuid4() for _ in range(count)]

def format_results(operation: str, raw_time: float, proxy_time: float, iterations: int) -> str:
    """Format benchmark results."""
    overhead = ((proxy_time - raw_time) / raw_time) * 100
    return (f"{operation:<20} | {raw_time:.6f}s | {proxy_time:.6f}s | "
            f"{overhead:+.2f}% | {iterations:,} ops")

class PerformanceTester:
    """Class to handle performance testing of AgentSet operations."""
    
    def __init__(self, test_size: int = 1000, iterations: int = 1000):
        """Initialize performance tester.
        
        Args:
            test_size: Number of UUIDs to use in tests
            iterations: Number of iterations for timing
        """
        self.test_size = test_size
        self.iterations = iterations
        self.test_uuids = generate_uuids(test_size)
        
        # Setup for raw AgentSet
        self.raw_set = AgentSet()
        
        # Setup for proxied AgentSet
        self.sim_agents = MockSimAgents()
        self.agent_state = TestAgentState(value=1)
        self.agent = TestAgent(self.agent_state, self.sim_agents)
        self.proxied_set = create_proxy_for_test(AgentSet(), self.agent)
    
    def reset_sets(self):
        """Reset both sets to empty state."""
        self.raw_set = AgentSet()
        self.proxied_set = create_proxy_for_test(AgentSet(), self.agent)
    
    def prepare_full_sets(self):
        """Fill both sets with all test UUIDs."""
        self.reset_sets()
        for uuid_val in self.test_uuids:
            self.raw_set.add(uuid_val)
            self.proxied_set.add(uuid_val)
    
    def benchmark_add(self) -> Tuple[float, float]:
        """Benchmark adding elements."""
        self.reset_sets()
        
        # Time adding to raw set
        raw_time = timeit.timeit(
            lambda: self.raw_set.add(uuid.uuid4()),
            number=self.iterations
        )
        
        # Time adding to proxied set
        proxy_time = timeit.timeit(
            lambda: self.proxied_set.add(uuid.uuid4()),
            number=self.iterations
        )
        
        return raw_time, proxy_time
    
    def benchmark_contains(self) -> Tuple[float, float]:
        """Benchmark contains check operation."""
        self.prepare_full_sets()
        
        # Create sample UUIDs that are in the set
        sample_uuids = self.test_uuids[:100]
        
        # Time contains check on raw set
        raw_time = timeit.timeit(
            lambda: sample_uuids[0] in self.raw_set,
            number=self.iterations
        )
        
        # Time contains check on proxied set
        proxy_time = timeit.timeit(
            lambda: sample_uuids[0] in self.proxied_set,
            number=self.iterations
        )
        
        return raw_time, proxy_time
    
    def benchmark_remove(self) -> Tuple[float, float]:
        """Benchmark removal operation."""
        # Time removing from raw set
        raw_set = AgentSet(self.test_uuids)
        raw_time = timeit.timeit(
            lambda: raw_set.discard(self.test_uuids[0]),
            number=self.iterations
        )
        
        # Time removing from proxied set
        proxied_set = create_proxy_for_test(AgentSet(self.test_uuids), self.agent)
        proxy_time = timeit.timeit(
            lambda: proxied_set.discard(self.test_uuids[0]),
            number=self.iterations
        )
        
        return raw_time, proxy_time
    
    def benchmark_iteration(self) -> Tuple[float, float]:
        """Benchmark raw_iter iteration operation - comparing equivalent operations."""
        # Prepare full raw set
        raw_set = AgentSet(self.test_uuids[:100])
        
        # For the proxied set
        proxied_set = create_proxy_for_test(AgentSet(self.test_uuids[:100]), self.agent)
        
        # Time iterating through raw set using raw_iter
        raw_time = timeit.timeit(
            lambda: list(raw_set.raw_iter),
            number=self.iterations
        )
        
        # Time iterating through proxied set using raw_iter for equivalent comparison
        proxy_time = timeit.timeit(
            lambda: list(proxied_set.raw_iter),
            number=self.iterations
        )
        
        return raw_time, proxy_time

    def benchmark_full_iteration(self) -> Tuple[float, float]:
        """Benchmark full iteration operation (raw_iter vs agent lookup)."""
        # Prepare full raw set
        raw_set = AgentSet(self.test_uuids[:100])
        
        # For the proxied set, we need agents in the mock SimAgents
        proxied_set = create_proxy_for_test(AgentSet(self.test_uuids[:100]), self.agent)
        for uuid_val in self.test_uuids[:100]:
            # Add a dummy agent to the mock SimAgents for each UUID
            self.sim_agents._agents[uuid_val] = TestAgent(TestAgentState(value=1), self.sim_agents)
        
        # Time iterating through raw set using raw_iter
        raw_time = timeit.timeit(
            lambda: list(raw_set.raw_iter),
            number=self.iterations
        )
        
        # Time iterating through proxied set with full agent lookup
        proxy_time = timeit.timeit(
            lambda: list(proxied_set),  # Uses __iter__ which needs context
            number=self.iterations
        )
        
        return raw_time, proxy_time

    def run_benchmarks(self):
        """Run all benchmarks and display results."""
        print("\nPerformance comparison between raw AgentSet and proxied AgentSet (MutableFieldProxy)")
        print("=" * 80)
        print(f"Test size: {self.test_size:,} UUIDs, Iterations: {self.iterations:,}")
        print("=" * 80)
        print(f"{'Operation':<25} | {'Raw Time':<10} | {'Proxy Time':<10} | {'Overhead':<10} | {'Iterations'}")
        print("-" * 80)
        
        # Run all benchmark operations
        operations = [
            ("Add operation", self.benchmark_add),
            ("Contains check", self.benchmark_contains),
            ("Remove operation", self.benchmark_remove),
            ("UUID Iteration (raw_iter)", self.benchmark_iteration),
            ("Agent Lookup Iteration", self.benchmark_full_iteration)
        ]
        
        # Run each benchmark and print results
        for name, benchmark_func in operations:
            gc.collect()  # Force garbage collection between tests
            raw_time, proxy_time = benchmark_func()
            print(format_results(name, raw_time, proxy_time, self.iterations))
        
        print("=" * 80)
        print("\nNotes:")
        print("1. Raw AgentSet = direct usage of AgentSet without a context")
        print("2. Proxy AgentSet = AgentSet accessed through MutableFieldProxy")
        print("3. Overhead % = how much slower the proxied version is compared to raw")
        print("4. 'UUID Iteration' compares raw_iter in both cases (fair comparison of same operation)")
        print("5. 'Agent Lookup Iteration' compares raw_iter vs full agent lookup (showing real-world impact)")
        print("6. The proxied version adds update tracking which contributes to overhead")


def main():
    """Main entry point."""
    # Default test parameters
    test_size = 1000
    iterations = 10000
    
    # Parse command-line arguments for custom test parameters
    args = sys.argv[1:]
    if len(args) >= 1:
        try:
            test_size = int(args[0])
        except ValueError:
            print(f"Invalid test size: {args[0]}, using default: {test_size}")
    
    if len(args) >= 2:
        try:
            iterations = int(args[1])
        except ValueError:
            print(f"Invalid iterations: {args[1]}, using default: {iterations}")
    
    # Run the benchmarks
    tester = PerformanceTester(test_size=test_size, iterations=iterations)
    tester.run_benchmarks()


if __name__ == "__main__":
    main()