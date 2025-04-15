from types import MethodType
from typing import TYPE_CHECKING, Any, Optional, Self
from copy import copy

if TYPE_CHECKING:
    from ..agents import Agent

_MISSING = object()


class MutableBaseField:
    """Base class for mutable fields in the simulation."""    
    context: Optional[tuple[str, 'Agent']] = None
    _context_required_error = RuntimeError(
        "Current context is not set. Contextual actions can only be done after the context is set."
    )
    
    def __getstate__(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != 'context'}

    def set_context(self, attr: str, owner: 'Agent'):
        """Set the context for the field.
        This method should only be called internally by the `Agent` class.
        """
        self.context = (attr, owner)
    
    def copy(self) -> Self:
        """Returns a copy of the field."""
        return copy(self)


magic_methods = [
    '__iter__',
    '__contains__',
    '__len__',
    '__getitem__',
    '__setitem__',
    '__delitem__',
    '__str__',
]
layer_lookup = {}
instance_type_cache = {}

def create_proxy_instance_type(instance: MutableBaseField) -> type:
    """Set the class of the instance to a new type that inherits from both the proxy class
    and the field class, and creates an intercepting layer in the mro of the field class
    to make super calls to field parent classes work correctly.
    
    Forwards all magic methods from the field class to the Proxy. So that the proxy
    behaves like the field class.
    """
    # Check if the instance is already in the cache
    if instance.__class__ in instance_type_cache:
        return instance_type_cache[instance.__class__]
    
    instance_mro = instance.__class__.mro()
    if MutableBaseField not in instance_mro:
        raise TypeError("A mutable field must inherit MutableBaseField.")
    
    # Those are methods that will be added to the proxy class
    adding_magic_methods = {}
    # Those are methods that will be added intercepting layer of the mro
    # This makes sure that the field's parent classes methods still behave the same
    intercepting_methods = {}
    
    # Loop over all methods in the field instance
    for method_name in dir(instance):
        if method_name in magic_methods:
            # Create a new function that calls the method on the field instance
            def map_magic_method(self, *args, _method_name=method_name, **kwargs):
                method = self._field_attr(_method_name)
                return method(*args, **kwargs)
            adding_magic_methods[method_name] = map_magic_method
        
        def intercept_method(self, *args, _method_name=method_name, _instance_type=instance.__class__, **kwargs):
            if self._intercept_super:
                # Look up the method in the field's class hierarchy
                method = getattr(super(self._field.__class__, self._field), _method_name, _MISSING)
            else:
                # Retain default behaviour for when _intercept_super is set to False
                method = getattr(super(layer_lookup[_instance_type], self), _method_name, _MISSING)
            
            if method is _MISSING:
                raise AttributeError(f"'super' object has no attribute '{_method_name}'")
            
            return method(*args, **kwargs)  # type: ignore
        # Add the intercept method to the intercepting methods
        intercepting_methods[method_name] = intercept_method
    
    # Put the MutableBaseField class at the beginning of the MRO
    instance_mro.insert(0, MutableFieldProxy)

    InterceptLayer = type(f"{instance.__class__.__name__}_InterceptLayer", (), intercepting_methods)
    layer_lookup[instance.__class__] = InterceptLayer
    # Place the intercept layer just after MutableBaseField in the MRO
    instance_mro.insert(instance_mro.index(MutableBaseField) + 1, InterceptLayer)
    
    # Create the proxy class with the new MRO
    ProxyInstanceType = type(f"{instance.__class__.__name__}_Proxy", tuple(instance_mro), adding_magic_methods)
    # Store the proxy class in the cache so we don't have to create it again for the same field class
    instance_type_cache[instance.__class__] = ProxyInstanceType
    return ProxyInstanceType


class MutableFieldProxy:
    """Proxy class for mutable fields in the simulation.
    
    This class is to make sure that mutable fields never get directly modified
    when setting the context. Instead, the context is accessed through the proxy class.
    """
    context = None
    _field = None
    _initialized = False
    _intercept_super = False
    
    def __new__(cls, field: MutableBaseField, *args, **kwargs):
        return field.__class__.__new__(create_proxy_instance_type(field))
    
    def __init__(self, field: MutableBaseField, attr: str, owner: 'Agent'):
        # Initialize the proxy with the field and its context
        # super().__init__()
        self._field = field
        self.context = (attr, owner)
        self._initialized = True

    def _field_attr(self, name: str) -> Any:
        """Get an attribute in _field."""
        # Check if name is a valid attribute of field
        field = object.__getattribute__(self, '_field')
        if (value := getattr(field, name, _MISSING)) is _MISSING:
            raise AttributeError(f"{self.__class__.__name__} object has no attribute '{name}'")
        
        # If the attribute value is a method, bind it to the proxy instance
        if isinstance(value, MethodType):
            def give_context_wrapper(self, *args, _method_func=value.__func__, _context=self.context, **kwargs):
                """Add the _intercept_super attribute during execution of the method
                to allow intercepting super calls in the field class to have the
                self reference point to the proxy instance instead of the field instance.
                """
                self.context = _context
                try:
                    return _method_func(self, *args, **kwargs)
                finally:
                    self.context = None
            # Bind the method to the proxy instance
            return MethodType(give_context_wrapper, self._field)
        return value
    
    def __getattribute__(self, name: str) -> Any:
        if not object.__getattribute__(self, '_initialized'):
            return object.__getattribute__(self, name)
        
        # Retain normal behavior for attributes in MutableBaseField
        if name in MutableFieldProxy.__dict__:
            return object.__getattribute__(self, name)
        
        return self._field_attr(name)
    
    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._field})'
