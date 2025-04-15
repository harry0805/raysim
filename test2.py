import pickle

class test:
    def __init__(self, a):
        self.a = a
        self.b = None
    
    @staticmethod
    def wrapper(func):
        """Decorator to wrap a function with a context manager."""
        def wrapped_func(*args, _func=func, **kwargs):
            print("Entering wrapper")
            try:
                return _func(*args, **kwargs)
            finally:
                print("Exiting wrapper")
        return wrapped_func

    @wrapper
    def test_func(self):
        print("Inside test_func")
        self.b = 2
        return self.a + self.b

t = test(123)
b = t.test_func()
print(b)

dump = pickle.dumps(t)
loaded = pickle.loads(dump)
print(loaded)
print(loaded.a)
print(loaded.b)
print(loaded.test_func())