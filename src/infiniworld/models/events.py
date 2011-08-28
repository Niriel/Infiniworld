#! /usr/bin/python
"""Events for the World Model.

"""
from infiniworld.evtman import Event

# pylint: disable-msg=R0903
# Too few public methods.  Events don't need public methods.

class ViewAreaEvent(Event):
    """THIS EVENT IS NOT MEANT TO LAST."""
    attributes = ('area_id',)

class EntityCreatedEvent(Event):
    """A new entity exists in the world."""
    attributes = ('entity_id', )

class DestroyEntityRequest(Event):
    """An entity must be destroyed."""
    attributes = ('entity_id',)

class EntityDestroyedEvent(Event):
    """An entity is totally and definitively removed from the world."""
    attributes = ('entity_id',)

class ControlEntityEvent(Event):
    """The player now controls that entity."""
    attributes = ('entity_id', )

class MoveEntityRequest(Event):
    """An entity is pushed in a direction by a player."""
    to_log = False
    attributes = ('entity_id', 'force',)

class EntityMovedEvent(Event):
    """An entity is in a new position."""
    to_log = False
    attributes = ('entity_id', 'pos',)

class EntityStoppedEvent(Event):
    """An entity has stopped moving."""
    to_log = False
    attributes = ('entity_id',)

class EntityEnteredAreaEvent(Event):
    """An entity entered an area."""
    attributes = ('entity_summary',)

class EntityLeftAreaEvent(Event):
    """An entity left an area."""
    attributes = ('entity_id', 'area_id')

class AreaContentRequest(Event):
    """Send that when you need to know what an area contains."""
    attributes = ('area_id',)

class AreaContentEvent(Event):
    """Response to an AreaContentRequest."""
    attributes = ('area_id', 'entities', 'tilemap')

class EntitySummaryRequest(Event):
    """Ask the summary of an entity."""
    attributes = ('entity_id',)

class EntitySummaryEvent(Event):
    """Response to an EntitySummaryRequest."""
    # The entity_id is in the summary, no need to duplicate it by making it an
    # attribute of the event.
    attributes = ('summary', )

class AttackRequest(Event):
    """Player is trying to have his creature attack something."""
    attributes = ('attacker',)

class AttackEvent(Event):
    """A creature attacks another."""
    attributes = ('attacker', 'victim')
# pylint: enable-msg=R0903
