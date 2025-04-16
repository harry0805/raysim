# Create an instance of MyClass
int_obj = 123
str_obj = "123"

# Define functions to test isinstance and type
def test_isinstance():
    return isinstance(str_obj, str)

def test_type():
    return type(str_obj) is str

# Measure execution time using timeit
# isinstance_time = timeit.timeit(test_isinstance, number=1000000000000)
# type_time = timeit.timeit(test_type, number=100000000000000)

# Print results
# print(f"isinstance time: {isinstance_time:.6f} seconds")
# print(f"type time: {type_time:.6f} seconds")
