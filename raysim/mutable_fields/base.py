from types import MethodType
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..agents import Agent


class MutableBaseField:
    """Base class for mutable fields in the simulation."""    
    context: Optional[tuple[str, 'Agent']] = None
    _context_required_error = RuntimeError(
        "Current context is not set. Contextual actions can only be done in the MutableFieldProxy class."
    )

magic_methods = [
    '__iter__',
    '__contains__',
    '__len__',
    '__getitem__',
    '__setitem__',
    '__delitem__',
    '__str__',
]

_MISSING = object()
class MutableFieldProxy:
    """Proxy class for mutable fields in the simulation."""
    context = None
    
    def __init__(self, field: MutableBaseField, attr: str, owner: 'Agent'):
        """Give this set a reference to the `Agent` object it is owned by.
        This method should only be used internally by `Agent`.
        
        Parameters:
            attr: The attribute name for this `agentSet` in `AgentState` object.
            owner: The `Agent` object that has this `agentSet`.
        """
        self._field = field
        self.context = (attr, owner)
        
        # Monkey patch all the magic methods to use the proxied instance
        for method_name in magic_methods:
            # Check if the method exists in the field
            if not hasattr(field, method_name):
                continue
            
            # Create a new function and bind it to the proxy instance
            def map_magic_method(self, *args, **kwargs):
                method = getattr(self, method_name)
                return method(*args, **kwargs)
            setattr(self, method_name, MethodType(map_magic_method, self))

    def __getattr__(self, name: str) -> Any:
        # Block access to _field directly
        if name == '_field':
            raise AttributeError("Cannot access _field directly from the proxy class.")
        
        # Check if name is a valid attribute of field
        field = object.__getattribute__(self, '_field')
        if (attr := getattr(field, name, _MISSING)) is _MISSING:
            raise AttributeError(f"{self.__class__.__name__} object has no attribute '{name}'")
        
        # If the attribute is a method, bind it to the proxy instance
        if isinstance(attr, MethodType):
            original_function = attr.__func__
            return MethodType(original_function, self)
        
        return attr
    
    def __repr__(self) -> str:
        return f'MutableFieldProxy({self._field})'
