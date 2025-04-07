from types import MethodType


class Base:
    def method(self):
        print("Base.method called")
        return "Base"


class Child(Base):
    def method(self):
        print("Child.method called")
        result = super().method()
        print(f"super() in Child returned: {result}")
        return "Child + " + result


class Proxy:
    def __init__(self, target):
        self._target = target
        
        # Rebind the method from target to self
        original_method = target.method
        self.method = MethodType(original_method.__func__, self)
    
    def __getattr__(self, name):
        return getattr(self._target, name)


if __name__ == "__main__":
    print("NORMAL INHERITANCE TEST")
    print("-----------------------")
    child = Child()
    result = child.method()
    print(f"Result: {result}\n")
    
    print("PROXY WITH REBOUND METHOD TEST")
    print("-----------------------------")
    child = Child()
    proxy = Proxy(child)
    
    try:
        result = proxy.method()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    
    print("\nMODIFIED PROXY WITH __CLASS__ ATTRIBUTE")
    print("-------------------------------------")
    
    class BetterProxy:
        def __init__(self, target):
            self._target = target
            self.__class__ = type(target)
            
            # Rebind the method from target to self
            original_method = target.method
            self.method = MethodType(original_method.__func__, self)
    
    try:
        better_proxy = BetterProxy(Child())
        result = better_proxy.method()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    
    print("\nALTERNATIVE SOLUTION: DELEGATING TO TARGET")
    print("----------------------------------------")
    
    class DelegatingProxy:
        def __init__(self, target):
            self._target = target
            
            # Create a new method that calls the target's method
            def delegated_method(self, *args, **kwargs):
                return self._target.method(*args, **kwargs)
            
            self.method = MethodType(delegated_method, self)
    
    delegating_proxy = DelegatingProxy(Child())
    result = delegating_proxy.method()
    print(f"Result: {result}")