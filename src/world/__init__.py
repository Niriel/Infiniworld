"""World model."""
import geometry
import evtman

# pylint: disable-msg=R0903
# Too few public methods.  Events don't need public methods.
class CreateEntityRequest(evtman.Event):
    """THIS EVENT IS NOT MEANT TO LAST.
    
    It lets the player test the engine by creating an entity with a keypress.
    
    """
    # TODO: remove.

class EntityCreatedEvent(evtman.Event):
    """A new entity exists in the world."""
    attributes = ('entity_id',)

class EntityDestroyedEvent(evtman.Event):
    """An entity is totally and definitively removed from the world."""
    attributes = ('entity_id',)

class MoveEntityRequest(evtman.Event):
    """An entity is pushed in a direction by a player."""
    attributes = ('entity_id', 'force', )

class EntityMovedEvent(evtman.Event):
    """An entity is in a new position."""
    attributes = ('entity_id', 'pos', )

# pylint: enable-msg=R0903

class EntityModel(evtman.SingleListener):
    """An entity in Infiniworld is anything that can move."""
    def __init__(self, event_manager, entity_id):
        evtman.SingleListener.__init__(self, event_manager)
        self._entity_id = entity_id
        self._pos = geometry.Vector()
    def moveTo(self, pos):
        """Set the position of the entity."""
        self._pos.icopy(pos)
        self.post(EntityMovedEvent(self._entity_id, self._pos))
    def onMoveEntityRequest(self, event):
        """Push the entity according to the player's wish.

        This won't say there, it's only for the very first tests.

        """
        # TODO: remove.
        if event.entity_id == self._entity_id:
            self.moveTo(self._pos + event.force)

class WorldModel(evtman.SingleListener):
    """The unique and authoritative top-level representation of the game world.
    
    """
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._entity_id_max = -1
        self._entities = {}
    def createEntity(self):
        """Populate the world with a new entity."""
        self._entity_id_max += 1 
        entity_id = self._entity_id_max 
        entity = EntityModel(self._event_manager, entity_id)
        self._entities[entity_id] = entity
        self.post(EntityCreatedEvent(entity_id))
    def destroyEntity(self, entity_id):
        """Remove an entity from the world, forever."""
        entity = self._entities.pop(entity_id)
        entity.unregister()
        self.post(EntityDestroyedEvent(entity_id))
    def onCreateEntityRequest(self, unused):
        """Player wants to create a new entity.

        This is not meant to stay, it's only for testing purposes.

        """
        # TODO: remove.
        self.createEntity()
