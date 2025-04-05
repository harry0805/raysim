"""
Please complete the code below following those instructions:

When using the access_data method it should return an instance of Dataclass or something that
behaves the same but its properties should return the correct context, but access_data shouldn't
modify the instance's attributes, because when accessing the instance of Dataclass elsewhere
should remain the same (without context). Also, avoid using copy inside access_data method as
it will slow things down if there is frequent access to the instance.
"""

class Dataclass:
    _context_required_error = RuntimeError("Context is not set. Use set_context() to set it.")
    
    @property
    def owner(self) -> object:
        """Returns context 1"""
        if not self.has_context:
            raise self._context_required_error
        ...
    
    @property
    def attr_name(self) -> str:
        """Returns context 2"""
        if not self.has_context:
            raise self._context_required_error
        ...
    
    @property
    def has_context(self) -> bool:
        """Check if the context is set."""
        ...

class Accessor:
    some_owner = object()
    some_attr = "some_attr"
    
    def access_data(self, data: Dataclass):
        ...