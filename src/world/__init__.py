import geometry
import evtman

class CreateEntityRequest(evtman.Event):
    pass

class EntityCreatedEvent(evtman.Event):
    attributes = ('entity_id',)

class EntityDestroyedEvent(evtman.Event):
    attributes = ('entity_id',)

class MoveEntityRequest(evtman.Event):
    attributes = ('entity_id', 'force', )

class EntityMovedEvent(evtman.Event):
    attributes = ('entity_id', 'pos', )

class EntityModel(evtman.SingleListener):
    def __init__(self, event_manager, entity_id):
        evtman.SingleListener.__init__(self, event_manager)
        self._entity_id = entity_id
        self._pos = geometry.Vector()
    def moveTo(self, pos):
        self._pos.icopy(pos)
        self.post(EntityMovedEvent(self._entity_id, self._pos))
    def onMoveEntityRequest(self, event):
        if event.entity_id == self._entity_id:
            self.moveTo(self._pos + event.force)

class WorldModel(evtman.SingleListener):
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        #
        self._entity_id_max = -1
        self._entities = {}
    def createEntity(self):
        self._entity_id_max += 1 
        entity_id = self._entity_id_max 
        entity = EntityModel(self._event_manager, entity_id)
        self._entities[entity_id] = entity
        self.post(EntityCreatedEvent(entity_id))
    def destroyEntity(self, entity_id):
        entity = self._entities.pop(entity_id)
        entity.unregister()
        self.post(EntityDestroyedEvent(entity_id))
    def onCreateEntityRequest(self, unused):
        self.createEntity()
