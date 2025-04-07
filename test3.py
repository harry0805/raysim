import copy # Only needed if you want to copy the settings dict itself

class TemporaryAttributeProxy:
    """
    A proxy object that overlays temporary attribute values onto an original object
    without modifying the original or performing a deep copy.

    Accesses attributes first from the temporary overlay, then delegates
    to the original object. Methods called on the proxy are executed on
    the original object but will read attributes through the proxy's logic
    if they access self.attribute_name.
    """
    # __slots__ can slightly optimize memory and prevent accidental attribute creation
    # on the proxy instance itself, enforcing delegation.
    __slots__ = ('_original_obj', '_temp_settings_overlay', '__weakref__')

    def __init__(self, original_obj, temp_settings_overlay):
        # Use object.__setattr__ to bypass our own __setattr__ logic
        # Store the original object reference
        object.__setattr__(self, '_original_obj', original_obj)
        # Store a copy of the temporary settings to prevent external modification
        object.__setattr__(self, '_temp_settings_overlay', temp_settings_overlay.copy())
        super()

    def __getattr__(self, name):
        # Avoids recursion when accessing internal attributes
        if name in ('_original_obj', '_temp_settings_overlay'):
            raise AttributeError()

        temp_settings = object.__getattribute__(self, '_temp_settings_overlay')
        original_obj = object.__getattribute__(self, '_original_obj')

        # Check the temporary overlay first
        if name in temp_settings:
            # print(f"Proxy: Returning '{name}' from overlay") # Debugging line
            return temp_settings[name]

        # If not in overlay, delegate attribute access to the original object
        # This handles both regular attributes and method calls
        # print(f"Proxy: Delegating '{name}' to original") # Debugging line
        try:
            attr = getattr(original_obj, name)
        except AttributeError:
             # Make proxy more transparent on AttributeErrors
             raise AttributeError(f"'{type(original_obj).__name__}' object (accessed via proxy) has no attribute '{name}'") from None

        # If the attribute is a method bound to the original object,
        # we need to ensure 'self' inside that method still resolves
        # attributes through the proxy. Often, getattr() handles this correctly,
        # but complex cases might require method wrapping if methods bypass getattr.
        # For typical use cases where methods access self.other_attr, this works.
        return attr


    def __setattr__(self, name, value):
        # Decide how setting attributes on the proxy should behave:

        # Option 1: Modify the temporary overlay (allows changing temp values)
        # This is often the most intuitive behavior for a proxy layer.
        # print(f"Proxy: Setting overlay '{name}' = {value}") # Debugging line
        temp_settings = object.__getattribute__(self, '_temp_settings_overlay')
        temp_settings[name] = value

        # Option 2: Forbid setting attributes on the proxy directly
        # raise AttributeError(f"Cannot set attribute '{name}' on this read-only proxy view.")

        # Option 3: Delegate to the original object (BE CAREFUL: Modifies the original!)
        # original_obj = object.__getattribute__(self, '_original_obj')
        # setattr(original_obj, name, value) # This violates the "don't modify original" rule

    def __delattr__(self, name):
        # Decide how deleting attributes on the proxy should behave:

        # Option 1: Remove from the temporary overlay
        temp_settings = object.__getattribute__(self, '_temp_settings_overlay')
        if name in temp_settings:
            # print(f"Proxy: Deleting '{name}' from overlay") # Debugging line
            del temp_settings[name]
        else:
            # If you want deletion to pass through ONLY if not in overlay (Careful!)
            # original_obj = object.__getattribute__(self, '_original_obj')
            # try:
            #     delattr(original_obj, name) # This violates the "don't modify original" rule
            # except AttributeError:
            #      raise AttributeError(f"Attribute '{name}' not found in temporary settings or original object.") from None

            # Safert: Only allow deletion of overridden attributes
             raise AttributeError(f"Attribute '{name}' not found in temporary settings overlay.")


    # Optional: Make the proxy more transparent for debugging/inspection
    def __repr__(self):
        original_obj = object.__getattribute__(self, '_original_obj')
        temp_settings = object.__getattribute__(self, '_temp_settings_overlay')
        return f"<TemporaryAttributeProxy for {original_obj!r} with overrides {temp_settings!r}>"

    def __str__(self):
        # Often delegating str() to the original is reasonable
        original_obj = object.__getattribute__(self, '_original_obj')
        return str(original_obj)

    # You might need to implement other magic methods (__len__, __getitem__, etc.)
    # if the original object uses them and you need the proxy to support them.
    # Often, __getattr__ handles delegating calls to the original's magic methods too.


# --- Your function ---
def create_temporarily_modified_proxy(original_obj, temp_settings):
    """
    Creates and returns a proxy object that behaves like the original
    but with specified attributes overridden by temp_settings.
    The original object is NOT modified.

    Args:
        original_obj: The original object instance (potentially large).
        temp_settings (dict): A dictionary where keys are attribute names
                              and values are the temporary values.

    Returns:
        An instance of TemporaryAttributeProxy wrapping the original object.
    """
    if not isinstance(temp_settings, dict):
        raise TypeError("temp_settings must be a dictionary")
    return TemporaryAttributeProxy(original_obj, temp_settings)

# --- Example Usage ---

class BigObject:
    def __init__(self, data, setting_a='default_a', setting_b=100):
        self.data = data # Assume this is large
        self.setting_a = setting_a
        self.setting_b = setting_b
        print(f"Original Initialized: data size={len(data)}, a={self.setting_a}, b={self.setting_b}")

    def process(self):
        # Method reads instance attributes
        print(f"  Processing with: a={self.setting_a}, b={self.setting_b}")
        # Simulate work
        return self.setting_b * 2

    def get_setting_a(self):
        return self.setting_a

    def __repr__(self):
        return f"BigObject(data_size={len(self.data)}, a='{self.setting_a}', b={self.setting_b})"

# Simulate large data
large_data = list(range(10000))
original = BigObject(large_data)

print("\n--- Original Object ---")
print(repr(original))
result_orig = original.process()
print(f"Original result: {result_orig}")
print(f"Original setting_a via method: {original.get_setting_a()}")

print("\n--- Create Proxy ---")
temporary_changes = {
    'setting_a': 'temporary_value',
    'setting_b': 555
}
proxy_obj = create_temporarily_modified_proxy(original, temporary_changes)

print("\n--- Using Proxy Object ---")
print(repr(proxy_obj))
# Access overridden attributes directly
print(f"Proxy setting_a (direct access): {proxy_obj.setting_a}")
print(f"Proxy setting_b (direct access): {proxy_obj.setting_b}")
# Access original attribute via proxy
print(f"Proxy data size (delegated access): {len(proxy_obj.data)}")

# Call method on proxy - the method executes on the original,
# but attribute lookups (self.setting_a, self.setting_b) inside it
# get intercepted by the proxy's __getattr__
result_proxy = proxy_obj.process()
print(f"Proxy result: {result_proxy}")
print(f"Proxy setting_a via method: {proxy_obj.get_setting_a()}")

# Try setting an attribute on the proxy (using Option 1 in __setattr__)
print("\n--- Modifying Proxy's Overlay ---")
proxy_obj.setting_a = 'another_temp_value'
proxy_obj.new_setting = 'added via proxy'
print(f"Proxy setting_a after change: {proxy_obj.setting_a}")
print(f"Proxy new_setting: {proxy_obj.new_setting}")
# Verify the original object is untouched
print("\n--- Verifying Original Object Unchanged ---")
print(repr(original))
print(f"Original setting_a: {original.setting_a}")
print(f"Original setting_b: {original.setting_b}")
print(f"Original has 'new_setting'?: {hasattr(original, 'new_setting')}") # Should be False
result_orig_after = original.process() # Should use original values
print(f"Original result after proxy use: {result_orig_after}")