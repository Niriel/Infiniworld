#! /usr/bin/python
"""Exceptions raised by the infiniworld models.

"""
# I had to create a specific module in order to avoid circular dependencies.
class WorldError(RuntimeError):
    """Base exception class for the world package."""
class AlreadyInAreaError(WorldError):
    """The area already contains what you are trying to add to it."""
class NotInAreaError(WorldError):
    """The area does not contain that object."""
