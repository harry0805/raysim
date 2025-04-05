import contextvars
from contextlib import contextmanager

# A context variable to store and retrieve the context implicitly
_current_context = contextvars.ContextVar("current_context")

class Context:
    def __init__(self, owner, attr_name):
        self.owner = owner
        self.attr_name = attr_name

@contextmanager
def use_context(owner, attr_name):
    """ Simple context manager setting context implicitly """
    token = _current_context.set(Context(owner, attr_name))
    try:
        yield
    finally:
        _current_context.reset(token)

class Dataclass:
    _context_required_error = RuntimeError("Context is not set. Use set_context() to set it.")

    @property
    def has_context(self):
        try:
            _current_context.get()
            return True
        except LookupError:
            return False

    @property
    def owner(self):
        if not self.has_context:
            raise self._context_required_error
        return _current_context.get().owner

    @property
    def attr_name(self):
        if not self.has_context:
            raise self._context_required_error
        return _current_context.get().attr_name

    # Example method inside Dataclass that utilizes internal context access
    def internal_method_using_context(self):
        # Can access owner and attr_name internally whenever context is set implicitly
        return f"Owner: {self.owner}, Attr: {self.attr_name}"

class Accessor:
    some_owner = object()
    some_attr = "some_attr"

    @contextmanager
    def access_data(self, data: Dataclass):
        """ 
        Access data contextually within a block; returns the same data object 
        but temporarily sets implicit context without modifying data.
        """
        with use_context(owner=self.some_owner, attr_name=self.some_attr):
            yield data  # Yielding the same original instance without copying or mutation


data = Dataclass()
accessor = Accessor()

# Without context: methods/properties should raise an error.
try:
    print(data.owner)
except RuntimeError as e:
    print(e)  # Context is not set. Use set_context() to set it.

# Use the context internally when calling methods:
with accessor.access_data(data) as ctx_data:
    print(ctx_data.owner)  # Works fine, prints 'accessor.some_owner'
    print(ctx_data.attr_name)  # Works fine, prints 'some_attr'
    print(ctx_data.internal_method_using_context())  # Internally method access is valid

# After context exits, data is unchanged, context is no longer available:
try:
    print(data.owner)
except RuntimeError as e:
    print(e)  # Context is not set. Use set_context() to set it.