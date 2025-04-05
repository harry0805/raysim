# class Test:
#     def __getattribute__(self, name):
#         print(f"Accessing: {name}")
#         return super().__getattribute__(name)

#     def __iter__(self):
#         return iter([1, 2, 3])

#     def __getitem__(self, index):
#         return [10, 20, 30][index]

# t = Test()

# # Implicit calls may bypass __getattribute__
# for x in t:   # Calls __iter__, but may not print "Accessing: __iter__"
#     print(x)

# print(t[1])   # Calls __getitem__, but may not print "Accessing: __getitem__"
