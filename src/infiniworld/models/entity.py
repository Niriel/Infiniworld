#! /usr/bin/python
"""EntityModel.

"""
# Standard library.
import logging
import weakref
# My stuff.
import events
from infiniworld.evtman import SingleListener
from infiniworld import geometry
from infiniworld import physics
import materials

LOGGER = logging.getLogger('world')

def existing(entities):
    """Use this generator to filter entity models on their existence status."""
    for entity in entities:
        if entity.exists:
            yield entity

class EntityModel(SingleListener):
    """An entity in Infiniworld is anything that can move."""
    NAME = 'Entity'
    BODY_MASS = 1 # kg.
    BODY_RADIUS = 0.5 # m.
    WALK_STRENGTH = 0 # N.
    SOLID = True
    def __init__(self, event_manager, entity_id):
        SingleListener.__init__(self, event_manager)
        self.entity_id = entity_id
        self._area = None
        self._age = 0
        # This `exists` variable is funny.  It comes in play because of how the
        # physics engine is built.  Imagine that for some reason (creature
        # walks in lava, bonus gets picked up), an entity disappears from the
        # world due to its physical interaction with the environment.  The
        # natural thing to do is to remove that entity from the world. However,
        # that will break the physics engine since the dictionaries will change
        # size during iterations.  So instead, we mark the 'dead' entity by
        # setting its `exists` variable to False.  That saves the physics
        # engine, but now we must take care that it ignores every entity that
        # does not exist.
        self.exists = True
        # Physics.
        self.body = physics.CircularBody(self.BODY_MASS,
                                         geometry.Vector(),
                                         self.SOLID,
                                         materials.MATERIAL_FLESH,
                                         self.BODY_RADIUS)
        self._walk_force = physics.ConstantForce(geometry.Vector())
        self.friction_force = physics.KineticFrictionForce(0)
        self.body.forces.add(self._walk_force)
        self.body.forces.add(self.friction_force)
        self._walk_strentgh = self.WALK_STRENGTH
        self.is_moving = False
        # Final stuff.
        self.post(events.EntityCreatedEvent(entity_id))
        LOGGER.debug("Entity %i created.", entity_id)

    def _getArea(self):
        """Return the AreaModel containing this EntityModel."""
        if self._area is None:
            return None
        return self._area()
    def _setArea(self, area_model):
        """Tell this EntityModels that it is contained by that AreaModel."""
        if area_model is None:
            self._area = None
        else:
            self._area = weakref.ref(area_model)
    area = property(_getArea, _setArea, None, "AreaModel for this entity.")

    def _getAreaId(self):
        """Return the area id of the area model containing this entity."""
        area = self.area
        if area is None:
            return None
        return area.area_id
    area_id = property(_getAreaId, None, None,
                       "Id of the area containing this entity.")

    def makeSummary(self):
        """Return a dictionary with enough info the the View to work with."""
        return {"entity_id" : self.entity_id,
                "name" : self.NAME,
                "area_id" : self.area_id,
                "pos": self.body.pos.copy()}

    def runAI(self, timestep):
        """Artificial intelligence."""
        # Obviously pretty stupid.

    def reactToCollision(self, collider):
        """The `collider` entity bumped into us."""
        # Don't care.

    def onMoveEntityRequest(self, event):
        """Push the entity according to the player's wish."""
        if event.entity_id == self.entity_id:
            self._walk_force.vector = event.force * self._walk_strentgh

    def onRunPhysicsEvent(self, event):
        """Time passes."""
        if self.area_id is not None:
            self._age += event.timestep
            self.runAI(event.timestep)
