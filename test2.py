class MySuper(super):
    pass

class Base:
    def greet(self):
        print("Hello from Base")

class FriendlyMixin:
    def greet(self):
        print("FriendlyMixin says hi")
        MySuper().greet()

class EnthusiasticMixin:
    def greet(self):
        print("EnthusiasticMixin is excited!")
        MySuper().greet()

class Greeter(EnthusiasticMixin, FriendlyMixin, Base):
    def greet(self):
        print("Greeter starting")
        MySuper().greet()

g = Greeter()
g.greet()