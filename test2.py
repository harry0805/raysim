from typing import Callable, TypeVar, Any
import types

class Dataclass:
    def __init__(self, name):
        self.name = name
        self._internal_data = f"Internal data for {name}"
        
        # Initialize context-related attributes for direct access
        # These will be None/False when accessed directly.
        # The proxy will override these when accessed via the proxy.
        self.owner: object | None = None
        self.attr_name: str | None = None
        self.has_context: bool = False # Direct access has no context

    def __repr__(self):
        return f"Dataclass(name={self.name})"
    
    def original_method(self) -> str:
        """An example method on the original class."""
        return f"Original method called on {self.name}"
    
    def some_method(self):
        # Check if context attributes are set (they won't be for direct access)
        # When called via the proxy, self will be the proxy, and these
        # attributes will have the context values provided by the proxy.
        if self.has_context and self.owner is not None and self.attr_name is not None:
            # Use the attributes directly
            owner = self.owner 
            attr_name = self.attr_name
            return f"My context is owner={owner} and attr_name='{attr_name}'"
        else:
            # Context is not set (either called directly on Dataclass,
            # or potentially on a proxy that wasn't set up correctly)
            return "My context is not set."

class DataclassProxy:
    """
    A proxy that wraps a Dataclass instance and provides contextual
    values for specific attributes ('owner', 'attr_name'). Methods called
    via the proxy will operate within this context.
    """
    def __init__(self, original_data: Dataclass, owner: object, attr_name: str):
        object.__setattr__(self, '_proxy_original_data', original_data)
        
        # Set context attributes directly on the proxy instance
        # These will shadow the corresponding attributes of the original_data
        # when accessed via the proxy.
        self.owner = owner
        self.attr_name = attr_name
        self.has_context = True

    def __getattr__(self, name: str) -> Any:
        """
        Delegates attribute access to the original object, ensuring methods
        are bound to the proxy instance ('self') so they operate within its context.
        """
        if name.startswith('_proxy_') or name in ('owner', 'attr_name', 'has_context'):
             # Raise AttributeError if trying to access proxy's own attributes via getattr
             # This prevents infinite loops if e.g. self.owner wasn't set in __init__
             raise AttributeError(f"Attribute '{name}' not found via __getattr__")

        try:
            target_attr = getattr(self._proxy_original_data, name)
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' (wrapping '{type(self._proxy_original_data).__name__}') object has no attribute '{name}'") from None

        if isinstance(target_attr, types.MethodType) and target_attr.__self__ is self._proxy_original_data:
            original_function = target_attr.__func__
            bound_method = types.MethodType(original_function, self)
            return bound_method
        
        return target_attr

    def __repr__(self) -> str:
        return f"DataclassProxy(wrapping={self._proxy_original_data!r})"

    def __str__(self) -> str:
        return str(self._proxy_original_data)

T = TypeVar('T')

class Accessor:
    some_owner = object()
    some_attr = "accessor_attribute"
    
    def access_data(self, data: Dataclass) -> DataclassProxy: 
        """
        Returns a proxy object wrapping the Dataclass instance.
        The proxy provides contextual values for 'owner' and 'attr_name'.
        """
        return DataclassProxy(data, self.some_owner, self.some_attr)

# Create instances
accessor = Accessor()
data1 = Dataclass('data1')

# Access the original object directly - context is not present
print(f"\nDirect access to data1:")
print(f"Data1 Owner: {data1.owner}") # Should now be None
print(f"Data1 Attr Name: {data1.attr_name}") # Should now be None
print(f"Data1 Has Context: {data1.has_context}") # Should be False
print(f"Data1 Some Method: {data1.some_method()}") # Should print "My context is not set."
print(f"Data1 Name: {data1.name}") # Accesses original directly

# --- Proxy Access Verification ---
proxy1 = accessor.access_data(data1)
print(f"\nProxy access to proxy1:")
print(f"Proxy1 Owner: {proxy1.owner}") # Should be accessor.some_owner
print(f"Proxy1 Attr Name: {proxy1.attr_name}") # Should be accessor.some_attr
print(f"Proxy1 Has Context: {proxy1.has_context}") # Should be True
print(f"Proxy1 Some Method: {proxy1.some_method()}") # Should print context info
print(f"Proxy1 Name: {proxy1.name}") # Delegated
print(f"Proxy1 Original Method: {proxy1.original_method()}") # Delegated & rebound

# Identity Checks
print(f"\nIdentity Checks:")
print(f"Is proxy1 the same instance as data1? {proxy1 is data1}")
print(f"Is proxy1 an instance of Dataclass? {isinstance(proxy1, Dataclass)}")
print(f"Is proxy1 an instance of DataclassProxy? {isinstance(proxy1, DataclassProxy)}")