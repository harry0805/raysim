import ray
import random
import time
from fractions import Fraction

# Let's start Ray
ray.init()

@ray.remote
def pi4_sample(sample_count):
    """pi4_sample runs sample_count experiments, and returns the 
    fraction of time it was inside the circle. 
    """
    in_count = 0
    for i in range(sample_count):
        x = random.random()
        y = random.random()
        if x*x + y*y <= 1:
            in_count += 1
    return Fraction(in_count, sample_count)

print('Starting...')
SAMPLE_COUNT = 10**9
BATCH_SIZE = 10**5
results = []
start = time.time()
for _ in range(int(SAMPLE_COUNT / BATCH_SIZE)):
    results.append(pi4_sample.remote(BATCH_SIZE))
output = ray.get(results)
end = time.time()
dur = end - start
print(f'Running {SAMPLE_COUNT} tests took {dur} seconds')
print(f'Estimated pi: {float(4 * sum(output) / len(output))}')