#! /usr/bin/python
"""Define models that are specific to the Apocalypse Bunny game.

"""
from __future__ import division
import math
import random
from operator import itemgetter
from infiniworld.events import StatusTextEvent
from infiniworld.evtman import Event
from infiniworld.evtman import SingleListener
from infiniworld.models import EntityModel
from infiniworld.models.events import DestroyEntityRequest
from infiniworld.models.events import AttackEvent
from infiniworld.geometry import Vector

#---------------------------------  Events.  ----------------------------------

# pylint: disable-msg=R0903
# Events don't need tons of method, so STFU pylint.
class HealthRequest(Event):
    """Asking how healthy a creature is."""
    attributes = ('entity_id',)

class HealthEvent(Event):
    """The health of a creature changed."""
    attributes = ('entity_id', 'amount')

class CarrotEvent(Event):
    """The bunny ate a carrot!"""
    attributes = ('amount',)

class ShockWaveEvent(Event):
    """The bunny casts a psy wave."""
    attributes = ('entity_id',)

class CreatureDiedEvent(Event):
    """A creature died."""
    attributes = ('entity_id',)

# pylint: enable-msg=R0903

#--------------------------------  Creatures.  --------------------------------

class CreatureModel(EntityModel):
    """Common base for entities that act like living creatures."""
    NAME = ''
    MAX_HEALTH = 1
    DAMAGE_COOLDOWN = .5
    ATTACK_COOLDOWN = .5
    def __init__(self, event_manager, entity_id):
        EntityModel.__init__(self, event_manager, entity_id)
        self._attack_cooldown = 0
        self._damage_cooldown = 0
        self._health_max = self.MAX_HEALTH
        self._health = self._health_max
    def die(self):
        """Argl."""
        # SUPER important: setting exists to False makes the rest of the engine
        # stop caring about this entity.  It will be removed from the world
        # later, but for now we have to skip it.
        self.exists = False
        # SUPER important too: posts the CreatureDiedEvent BEFORE the
        # DestroyEntityRequest.
        self.post(CreatureDiedEvent(self.entity_id))
        self.post(DestroyEntityRequest(self.entity_id))
    def setHealth(self, health):
        """Set the health level, within limits, posts if changed, die too."""
        old_health = self._health
        self._health = health
        if self._health < 0:
            self._health = 0
        if self._health > self._health_max:
            self._health = self._health_max
        if self._health != old_health:
            self.post(HealthEvent(self.entity_id, self._health))
            if self._health == 0:
                self.die()
    def changeHealth(self, offset):
        """Shortcut for setting the health with a relative value."""
        self.setHealth(self._health + offset)
    def runAI(self, timestep):
        """Basic AI of creatures."""
        self._damage_cooldown -= timestep
        if self._damage_cooldown < 0:
            self._damage_cooldown = 0
        self._attack_cooldown -= timestep
        if self._attack_cooldown < 0:
            self._attack_cooldown = 0
    def onHealthRequest(self, event):
        """Medical files are public domain."""
        if event.entity_id == self.entity_id:
            self.post(HealthEvent(self.entity_id, self._health))
    def onAttackEvent(self, event):
        """We're under attack!"""
        if event.victim == self.entity_id:
            if self._damage_cooldown == 0:
                self._damage_cooldown = self.DAMAGE_COOLDOWN
                self.changeHealth(-1)

class BunnyModel(CreatureModel):
    """Our hero !"""
    NAME = 'Bunny'
    BODY_MASS = 1
    BODY_RADIUS = 0.3
    WALK_STRENGTH = 50
    DAMAGE_COOLDOWN = .5
    ATTACK_COOLDOWN = .3
    MAX_HEALTH = 10
    def __init__(self, event_manager, entity_id):
        CreatureModel.__init__(self, event_manager, entity_id)
        self._carrots = 0
    def setCarrots(self, value):
        """Inventory management :D."""
        self._carrots = value
        self.post(CarrotEvent(self._carrots))
    def giveCarrot(self):
        """Shortcut for picking up a carrot."""
        # This is called by the CarrotModel when it is collided by a bunny.
        self.setCarrots(self._carrots + 1)
    def onAttackRequest(self, event):
        """Player wants us to attack."""
        if event.attacker != self.entity_id:
            return
        if self._attack_cooldown > 0:
            self.post(StatusTextEvent("Too soon!"))
            return
        if not self._carrots:
            self.post(StatusTextEvent("Not enough carrots!"))
            return
        self._attack_cooldown = self.ATTACK_COOLDOWN
        self.post(StatusTextEvent("Psy-wave!"))
        # This is going to make the view display a special effect showing
        # the psy wave.
        self.post(ShockWaveEvent(self.entity_id))
        self.setCarrots(self._carrots - 1)
        entities = self.area.entity_map.getNear(self.body.pos, 8)
        impulse_max = 20
        for entity in entities:
            if not (entity.exists and entity.body.solid):
                continue
            if entity == self:
                continue
            difference = entity.body.pos - self.body.pos
            try:
                impulse = (60 * entity.body.one_over_mass /
                           difference.norm() ** .5)
            except ZeroDivisionError:
                impulse = impulse_max
            impulse = difference.normalized() * impulse
            entity.body.vel += impulse
            # The shock is so strong the creature may be hurt.
            if impulse.norm() >= impulse_max * .6:
                self.post(AttackEvent(self.entity_id, entity.entity_id))

class ZombieFoxModel(CreatureModel):
    """Enemies, they're evil."""
    NAME = 'Zombie fox'
    BODY_MASS = 3
    BODY_RADIUS = 0.5
    WALK_STRENGTH = 30
    MAX_HEALTH = 1
    PERCEPTION_RADIUS = 4
    ATTACK_RADIUS = (BODY_RADIUS + BunnyModel.BODY_RADIUS) * 1.1
    CHANGE_DIRECTION_COOLDOWN = 2
    def __init__(self, event_manager, entity_id):
        CreatureModel.__init__(self, event_manager, entity_id)
        self._change_direction_cooldown = 0
    def randomWalk(self):
        """Goes somewhere stupidely, like zombies do."""
        self._change_direction_cooldown = self.CHANGE_DIRECTION_COOLDOWN
        self._change_direction_cooldown *= .8 + .4 * random.random()
        angle = random.random() * 2 * math.pi
        self._walk_force.vector = Vector.fromDirection(angle,
                                                       self.WALK_STRENGTH)
    def runAI(self, timestep):
        CreatureModel.runAI(self, timestep)
        self._change_direction_cooldown -= timestep
        if self._change_direction_cooldown < 0:
            self._change_direction_cooldown = 0

        # Looking for nearby bunnies.
        entities = self.area.entity_map.getNear(self.body.pos,
                                                self.PERCEPTION_RADIUS)
        entities = [entity
                    for entity in entities
                    if entity.NAME == 'Bunny' and entity.exists]
        if entities:
            # Sort by distance.
            distances = [entity.body.pos.dist(self.body.pos)
                         for entity in entities]
            entities = zip(entities, distances)
            entities.sort(key=itemgetter(1))
            # The closest.
            bunny, distance = entities[0]
            direction = (bunny.body.pos - self.body.pos).normalized()
            if distance <= self.ATTACK_RADIUS and self._attack_cooldown == 0:
                self._attack_cooldown = self.ATTACK_COOLDOWN
                self._walk_force.vector.zero()
                self.post(AttackEvent(self.entity_id, bunny.entity_id))
            else:
                self._walk_force.vector = direction * self.WALK_STRENGTH
        elif self._change_direction_cooldown == 0:
            self.randomWalk()

#----------------------------------  Items.  ----------------------------------

class CarrotModel(EntityModel):
    """Radioactive food !"""
    NAME = 'Carrot'
    BODY_MASS = 1
    SOLID = False
    BODY_RADIUS = 0.5
    WALK_STRENGTH = 30
    def reactToCollision(self, collider):
        """The `collider` entity bumped into us."""
        if collider.NAME == 'Bunny':
            self.exists = False
            self.post(DestroyEntityRequest(self.entity_id))
            collider.giveCarrot()
            collider.changeHealth(1)
            self.post(StatusTextEvent('Om nom nom!'))

#---------------------------------  Spawner.  ---------------------------------

class SpawnerModel(SingleListener):
    """This creates entities as the time goes."""
    def __init__(self, event_manager):
        SingleListener.__init__(self, event_manager)
        self.area = None
        self.coords = None
        self.factory = None
        self.period = None
        self._timer = 0
        self._active = True
    def spawn(self):
        """Create an entity."""
        world = self.area.world
        entity = world.createEntity(self.factory)
        # I have to put the set of coords into a list otherwise random.choice
        # doesn't work.
        entity.body.pos = Vector(random.choice(list(self.coords)))
        world.moveEntityToArea(entity.entity_id, self.area.area_id)
    def onRunPhysicsEvent(self, event):
        """Create entities if it is time to do so"""
        if not self._active:
            return
        self._timer += event.timestep
        how_many, self._timer = divmod(self._timer, self.period)
        for unused in xrange(int(how_many)):
            self.spawn()
    def onGameOverEvent(self, unused):
        """Don't create anything anymore when the game is over."""
        self._active = False
