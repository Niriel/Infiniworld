"""Code that is specific to pygame."""
from __future__ import division
import pygame
import events
import evtman
import geometry
import world # For its events ONLY.

import logging

logger = logging.getLogger('pygame')

class Pygame(object):
    """Context manager that initializes and closes PyGame properly."""
    def __enter__(self):
        unused, numfail = pygame.init()
        if numfail:
            print "%i Pygame module(s) could not be initialized." % numfail
    def __exit__(self, *unused):
        surface = pygame.display.get_surface()
        if surface:
            # Pygame can need a couple of seconds to close and we don't want
            # the game to appear frozen.  So we erase the screen and display
            # a message explaining what's going on.
            font = pygame.font.Font(None, 32)
            text = font.render(u"Shutting down...", True, (255, 255, 255))
            surface.fill((0, 0, 0))
            surface.blit(text, (0, 0))
            pygame.display.flip()
        pygame.quit()


class PygameController(evtman.SingleListener):
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._old_vector = geometry.Vector()
    def scanKeyboard(self):
        x = y = 0
        key = pygame.key.get_pressed()
        if key[pygame.K_w]: y += 1
        if key[pygame.K_a]: x -= 1
        if key[pygame.K_s]: y -= 1
        if key[pygame.K_d]: x += 1
        vector = geometry.Vector((x, y))
        if x or y:
            vector.normalize()
        if vector != self._old_vector:
            self.post(events.PlayerMovedEvent(vector))
            self._old_vector = vector
    def pumpPygameEvents(self):
        for pygame_event in pygame.event.get():
            pygame_event_type = pygame_event.type
            if pygame_event_type != pygame.MOUSEMOTION:
                logger.debug(pygame_event)

            if pygame_event_type == pygame.QUIT:
                self.post(events.QuitRequest())

            elif pygame_event_type == pygame.KEYDOWN:
                key = pygame_event.key
                if key == pygame.K_ESCAPE:
                    self.post(events.QuitRequest())
                elif key == pygame.K_RETURN:
                    self.post(world.CreateEntityRequest())
        self.scanKeyboard()
    def onProcessInputsEvent(self, unused):
        self.pumpPygameEvents()


class PygameView(evtman.SingleListener):
    def __init__(self, event_manager, title, resolution):
        evtman.SingleListener.__init__(self, event_manager)
        self._surface = pygame.display.set_mode(resolution)
        pygame.display.set_caption(title)
        #
        self._area_view = AreaView(self._event_manager)
        self._area_view.sprite.rect.center = self._surface.get_rect().center
        #
        self._group = pygame.sprite.Group()
        self._group.add(self._area_view.sprite)
    def render(self):
        self._area_view.render()
        self._group.draw(self._surface)
        pygame.display.flip()
    def onRenderFrameEvent(self, unused):
        self.render()


class CoordinatesConverter(object):
    """Converts world coordinates to screen coordinates.

    To a fixed reference point on the screen corresponds a reference point in
    the world that can vary.  For example, you can wish to center the view on
    the character the player is controlling, so the center of the screen
    (fixed) corresponds to a varying world position.

    Furthermore, there is a conversion factor to translate distances in the
    world to a number of pixels on the screen.

    The world position is given by a geometry.Vector object because that is
    what is used in the physics engine.  However, these Vector objects are not
    practical for screen coordinates: pygame prefers Rect or tuples.  So we
    use tuples.

    """
    def __init__(self):
        object.__init__(self)
        self.zoom = 32
        # World coordinates are expected to be floats.
        self._ref_world = geometry.Vector()
        # While pixels are integers.
        self._ref_pix_x = 0
        self._ref_pix_y = 0
    def setRefWorld(self, vector):
        self._ref_world.icopy(vector)
    def setRefPix(self, xytuple):
        self._ref_pix_x, self._ref_pix_y = xytuple
    def worldToPix(self, pos):
        offset = (pos - self._ref_world) * self.zoom
        # The minus sign comes from my convention.  I consider that the world
        # Y axis increases when we move to the North.  However, the display
        # says otherwise.
        return (self._ref_pix_x + int(round(offset.x)),
                self._ref_pix_y - int(round(offset.y)))

class EntityView(evtman.SingleListener):
    def __init__(self, event_manager, entity_id):
        evtman.SingleListener.__init__(self, event_manager)
        self._entity_id = entity_id
        # World coordinates.
        self._pos = geometry.Vector()
        #
        self.sprite = None
        self.createSprite()
        self._dirty = True
    def createSprite(self):
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = pygame.Surface((32, 32))
        self.sprite.rect = self.sprite.image.get_rect()
    def render(self):
        if not self._dirty:
            return
        self.sprite.image.fill((255, 255, 255))
        self._dirty = False
    def setCoords(self, vector):
        self._pos.icopy(vector)
    def worldToPix(self, coord_conv):
        self.sprite.rect.center = coord_conv.worldToPix(self._pos)
    def onEntityMovedEvent(self, event):
        if event.entity_id == self._entity_id:
            self.setCoords(event.pos)

class AreaView(evtman.SingleListener):
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        # The area view displays the landscape, objects, entities, etc..
        self.sprite = None
        self.createSprite()
        # It owns the EntityViews.
        self._entities = {}
        # Entities have sprites that are added to this group for display
        # purposes.
        self._entities_group = pygame.sprite.Group()
        # We need something to convert world coordinates (in meters) to
        # screen coordinates (in pixels).
        self._coord_conv = CoordinatesConverter()
    def createSprite(self):
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = pygame.Surface((13 * 32, 13 * 32))
        self.sprite.rect = self.sprite.image.get_rect()
    def createEntityView(self, entity_id):
        entity_view = EntityView(self._event_manager, entity_id)
        self._entities_group.add(entity_view.sprite)
        self._entities[entity_id] = entity_view
    def destroyEntityView(self, entity_id):
        entity_view = self._entities.pop(entity_id)
        entity_view.unregister()
        self._entities_group.remove(entity_view.sprite)
    def render(self):
        image = self.sprite.image
        image.fill((64, 64, 64))
        for entity in self._entities.itervalues():
            entity.worldToPix(self._coord_conv)
            entity.render()
        self._entities_group.draw(image)
    def onEntityCreatedEvent(self, event):
        self.createEntityView(event.entity_id)
    def onEntityDestroyedEvent(self, event):
        self.destroyEntityView(event.entity_id)
