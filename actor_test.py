from typing import Any
import ray
import logging

logging.basicConfig(level=logging.INFO)

ray.init()

@ray.remote
class SharedObject:
    def __init__(self, initial_data):
        self.data = initial_data  # The large shared object
    
    def apply_update(self, updates):
        """Apply updates to the shared object."""
        for key, value in updates.items():
            self.data[key] = value  # Modify the object
    
    def get_data(self):
        return self.data  # Get the current state

# Initialize the actor with a large object
initial_data = {i: 0 for i in range(1000000)}  # Example large dictionary
shared_actor: Any = SharedObject.remote(initial_data)

@ray.remote
def compute_update(start, end):
    """Task computes an update (returns only the necessary modifications)."""
    logging.warning('test')
    updates = {i: i * 2 for i in range(start, end)}  # Example modification
    return updates  # Returning only the diff

# Launch parallel tasks that compute updates
tasks = [compute_update.remote(i * 10000, (i + 1) * 10000) for i in range(100)]
updates_list = ray.get(tasks)  # Gather all updates

# Apply updates to the shared object
update_futures = [shared_actor.apply_update.remote(upd) for upd in updates_list]
ray.get(update_futures)  # Wait for all updates to be applied

# Get the final modified object
final_data: dict = ray.get(shared_actor.get_data.remote())
print(list(final_data.items())[:10])  # Print first 10 elements