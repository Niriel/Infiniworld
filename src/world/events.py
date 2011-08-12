#! /usr/bin/python
"""Events for the World Model.

"""
from evtman import Event

# pylint: disable-msg=R0903
# Too few public methods.  Events don't need public methods.
class CreateEntityRequest(Event):
    """THIS EVENT IS NOT MEANT TO LAST."""
    # TODO: remove.

class CreateAreaRequest(Event):
    """THIS EVENT IS NOT MEANT TO LAST."""
    # TODO: remove.

class ViewNextAreaRequest(Event):
    """THIS EVENT IS NOT MEANT TO LAST."""
    # TODO: remove.
    attributes = ('area_id', 'offset')

class ViewAreaEvent(Event):
    """THIS EVENT IS NOT MEANT TO LAST."""
    # TODO: remove.
    attributes = ('area_id',)
    
class ControlNextEntityRequest(Event):
    """THIS EVENT IS NOT MEANT TO LAST."""
    # TODO: remove.
    attributes = ('entity_id', 'offset')

class ControlEntityEvent(Event):
    """THIS EVENT IS NOT MEANT TO LAST."""
    # TODO: remove.
    attributes = ('entity_id', )

class MoveEntityToNextAreaRequest(Event):
    """THIS EVENT IS NOT MEANT TO LAST."""
    # TODO: remove.
    attributes = ('entity_id', 'offset', )

class EntityCreatedEvent(Event):
    """A new entity exists in the world."""
    attributes = ('entity_id', )

class EntityDestroyedEvent(Event):
    """An entity is totally and definitively removed from the world."""
    attributes = ('entity_id',)

class MoveEntityRequest(Event):
    """An entity is pushed in a direction by a player."""
    attributes = ('entity_id', 'force',)

class EntityMovedEvent(Event):
    """An entity is in a new position."""
    attributes = ('entity_id', 'pos',)

class EntityEnteredAreaEvent(Event):
    """An entity entered an area."""
    attributes = ('entity_id', 'area_id', 'pos')

class EntityLeftAreaEvent(Event):
    """An entity left an area."""
    attributes = ('entity_id', 'area_id')

class AreaContentRequest(Event):
    """Send that when you need to know what an area contains."""
    attributes = ('area_id',)

class AreaContentEvent(Event):
    """Response to an AreaContentRequest."""
    attributes = ('area_id', 'entities', 'tilemap')

# pylint: enable-msg=R0903
