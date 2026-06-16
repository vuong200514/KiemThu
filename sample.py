"""Example source file with simple arithmetic functions used by tests."""

def sum(a, b):
    """Return the sum of two numbers."""
    return a + b


def multiply(a, b):
    """Return the product of two numbers."""
    return a * b


class Calculator:
    """Optional example class with methods."""

    def add(self, a, b):
        return sum(a, b)

    def mul(self, a, b):
        return multiply(a, b)