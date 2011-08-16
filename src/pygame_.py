"""Code that is specific to pygame."""
from __future__ import division
import logging
import math

import pygame

import events
import evtman
import geometry
import world # For its events ONLY.

LOGGER = logging.getLogger('pygame')

# pylint: disable-msg=R0903
# Too few public methods.  I know, it's just a Context Manager, they don't
# need anything more.
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

class FPSSprite(pygame.sprite.Sprite):
    """Sprite that displays the number of frames per second."""
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)
        self._clock = pygame.time.Clock()
        self._font = pygame.font.Font(None, 24)
        self._pos = pos
        self._old_fps = -1
        self.image = None
        self.rect = None
    def update(self):
        """Use the pygame clock to get the FPS, and makes an image for it."""
        self._clock.tick()
        fps = self._clock.get_fps()
        if fps == self._old_fps:
            return
        self._old_fps = fps
        text = "%i FPS" % fps
        self.image = self._font.render(text, True,
                                       (255, 255, 255), (32, 0, 32))
        self.rect = self.image.get_rect()
        self.rect.topleft = self._pos
# pylint: enable-msg=R0903

def draw3dBorder(image, color, thickness):
    """Welcome back to the 90s!
    
    `color` must be a (r, g, b) or (r, g, b, a) tuple.

    I wish you could give Color.__init__ a Color object as argument to make a
    copy or to stop worrying about types.  But no :(.

    """
    color_light = pygame.color.Color(*color)
    hsla = list(color_light.hsla)
    hsla[2] = min(int(hsla[2] * 1.2), 100)
    color_light.hsla = hsla
    #
    color_dark = pygame.color.Color(*color)
    hsla = list(color_dark.hsla)
    hsla[2] = int(hsla[2] * .8)
    color_dark.hsla = hsla
    #
    max_x, max_y = image.get_size()
    max_x -= 1
    max_y -= 1
    #
    for i in xrange(thickness):
        pygame.draw.line(image, color_light, (i, i), (max_x - i, i))
        pygame.draw.line(image, color_light, (i, i), (i, max_y - i - 1))
        pygame.draw.line(image, color_dark, (max_x - i, max_y - i),
                         (i, max_y - i))
        pygame.draw.line(image, color_dark, (max_x - i, max_y - i),
                         (max_x - i, i + 1))


def makeTileImages(elevation):
    """Generate beautiful bitmaps for displaying sprites."""
    size = (32, 32)
    # From http://hyperphysics.phy-astr.gsu.edu/hbase/vision/cie.html
    colors = {world.tile.NATURE_DEEPWATER: (92, 138, 202),
              world.tile.NATURE_DIRT: (152, 118, 84),
              world.tile.NATURE_GRASS: (0, 163, 71),
              world.tile.NATURE_SAND: (234, 231, 94),
              world.tile.NATURE_SHALLOWWATER: (110, 175, 199),
              world.tile.NATURE_STONE: (128, 128, 128)}
    images = {}
    for nature, color in colors.iteritems():
        # pylint: disable-msg=E1121
        # Too many positional arguments.  Nope.  Pylint's weird here.
        image = pygame.Surface(size)
        # pylint: enable-msg=E1121
        image.fill(color)
        if elevation == 1:
            draw3dBorder(image, color, 4)
        images[nature] = image
    return images
TILE_IMAGES_LOW = None
TILE_IMAGES_HIGH = None

class PygameController(evtman.SingleListener):
    """Reads the input from the keyboard and mouse from pygame."""
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._old_vector = geometry.Vector()

    def _scanKeyboard(self):
        """Look at what keys are actually pressed, and reacts."""
        # I found out that only looking at the KEYUP and KEYDOWN events was not
        # reliable.  These events are not created if the key was pushed or
        # released when the pygame window wasn't focused.  It is possible that
        # some application suddenly pops up and steal the keyboard focus, and
        # then you release your 'North' key but the game does not realize, and
        # when you go back to it you have to press and re-release North.  It
        # sucks.

        # So instead I just look at the keys that are actually pressed.  When
        # the pygame window loses the focus, all the keys are suddenly
        # considered 'unpressed' by SDL (I tested it).  Then, when I'm back in,
        # it will see whether or not I'm pressing something.

        x = y = 0
        key = pygame.key.get_pressed()
        # Move your character with WASD.
        # pylint: disable-msg=C0321
        # More than one statement on a single line.  Yeah but it's prettier.
        if key[pygame.K_w]: y += 1
        if key[pygame.K_a]: x -= 1
        if key[pygame.K_s]: y -= 1
        if key[pygame.K_d]: x += 1
        # pylint: enable-msg=C0321
        vector = geometry.Vector((x, y))
        if x or y:
            vector.normalize()
        if vector != self._old_vector:
            self.post(events.MoveCommand(vector.copy()))
            self._old_vector = vector

    def keyDown(self, key):
        """Process pygame KEYDOWN events."""
        if key == pygame.K_ESCAPE:
            self.post(events.QuitEvent())

        elif key == pygame.K_RETURN:
            self.post(events.CreateEntityCommand())
        elif key == pygame.K_SEMICOLON:
            self.post(events.ControlNextEntityCommand(-1))
        elif key == pygame.K_QUOTE:
            self.post(events.ControlNextEntityCommand(1))

        elif key == pygame.K_BACKSLASH:
            self.post(events.CreateAreaCommand())
        elif key == pygame.K_LEFTBRACKET:
            self.post(events.ViewNextAreaCommand(-1))
        elif key == pygame.K_RIGHTBRACKET:
            self.post(events.ViewNextAreaCommand(1))

        elif key == pygame.K_PERIOD:
            self.post(events.MoveEntityToNextAreaCommand(-1))
        elif key == pygame.K_SLASH:
            self.post(events.MoveEntityToNextAreaCommand(1))

    def pumpPygameEvents(self):
        """Process the events sent by pygame.

        It's best to call that very often to make sure that the application
        remains responsive.

        """
        for pygame_event in pygame.event.get():
            pygame_event_type = pygame_event.type
            if pygame_event_type != pygame.MOUSEMOTION:
                #LOGGER.debug(pygame_event)
                pass

            if pygame_event_type == pygame.QUIT:
                self.post(events.QuitEvent())

            elif pygame_event_type == pygame.KEYDOWN:
                self.keyDown(pygame_event.key)
        self._scanKeyboard()

    def onProcessInputsEvent(self, unused):
        """The main loop asks for inputs."""
        self.pumpPygameEvents()


class PygameView(evtman.SingleListener):
    """The root of everything that's going to be on screen."""
    def __init__(self, event_manager, title, resolution):
        evtman.SingleListener.__init__(self, event_manager)
        # For some reason, on Ubuntu 11.04, I cannot change the caption
        # of the window once it is created, only the caption in the task bar
        # is modified if I call set_caption after set_mode.
        pygame.display.set_caption(title)
        self._surface = pygame.display.set_mode(resolution)
        #
        self._area_view = AreaView(self._event_manager, (13 * 32, 13 * 32))
        self._area_view.sprite.rect.center = self._surface.get_rect().center
        #
        self._group = pygame.sprite.Group()
        self._group.add(self._area_view.sprite)
        #
        fps_sprite = FPSSprite((0, 0))
        self._group.add(fps_sprite)
    def render(self):
        """Display things on screen."""
        self._area_view.render()
        self._group.update()
        self._group.draw(self._surface)
        pygame.display.flip()
    def onRenderFrameEvent(self, unused):
        """The game loop asks us to draw something."""
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
    def setRefWorld(self, pos_vector):
        """Set the reference world coordinates.

        If you have defined the reference pixel coordinates to be the center
        of your view, then calling setRefWorld centers your view on the given
        position.  For example, setRefWorld(entity.pos) will center the world
        on that entity.

        """
        self._ref_world.icopy(pos_vector)
    def setRefPix(self, xytuple):
        """Set the reference pixel coordinates.

        Any tuple of two integers is valid.  However, very few are handy.
        The one I suggest is the middle point of the view area.  It allows
        you to very easily center the view on any point of the world.

        setRefPix(AreaView.sprite.rect.width // 2,
                  AreaView.sprite.rect.height // 2)

        """
        self._ref_pix_x, self._ref_pix_y = xytuple
    def worldToPix(self, pos_vector):
        """Convert world coordinates to pixel coordinates."""
        offset = (pos_vector - self._ref_world) * self.zoom
        # The minus sign comes from my convention.  I consider that the world
        # Y axis increases when we move to the North.  However, the display
        # says otherwise.
        return (self._ref_pix_x + int(round(offset.x)),
                self._ref_pix_y - int(round(offset.y)))
    def pixToWorld(self, (pix_x, pix_y)):
        """Return the world coordinates corresponding to the given pixel."""
        offset_x = pix_x - self._ref_pix_x
        offset_y = self._ref_pix_y - pix_y
        offset = geometry.Vector(offset_x, offset_y)
        pos_vector = offset / self.zoom + self._ref_world
        return pos_vector


class EntityView(evtman.SingleListener):
    """Managed the appearance of an entity on screen."""
    @classmethod
    def fromSummary(cls, event_manager, summary):
        """Alternative constructor for using a summary to configure the View.
        
        """
        instance = cls(event_manager, summary['entity_id'])
        instance.applySummary(summary)
        return instance

    def __init__(self, event_manager, entity_id):
        evtman.SingleListener.__init__(self, event_manager)
        self._entity_id = entity_id
        # World coordinates.
        self.pos = geometry.Vector()
        #
        self.sprite = None
        self.createSprite()
        self._dirty = True
    def applySummary(self, summary):
        """Configure the view using the info from the summary."""
        if summary['entity_id'] != self._entity_id:
            raise ValueError("entity_id mismatch")
        self.pos.icopy(summary['pos'])
    def createSprite(self):
        """Instantiate the sprite, its image and its rect."""
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        # Too many positional arguments for function call.
        # Somehow pylint is confused by Surface.
        self.sprite.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.sprite.rect = self.sprite.image.get_rect()
        # The position part of the rect is assigned by the AreaView.
    def render(self):
        """(Re)draw the image of the sprite.
        
        Only if necessary: if self._dirty is True.
        
        """
        if not self._dirty:
            return
        self.sprite.image.fill((0, 0, 0, 0)) # Transparent.
        pygame.draw.circle(self.sprite.image, (255, 255, 255, 255),
                           (16, 16), 16)
        font = pygame.font.Font(None, 24)
        text = str(self._entity_id)
        text_image = font.render(text, True, (64, 64, 64, 0))
        text_rect = text_image.get_rect()
        image_rect = self.sprite.image.get_rect()
        text_rect.center = image_rect.center
        self.sprite.image.blit(text_image, text_rect)
        self._dirty = False
    def setCoords(self, vector):
        """Set the world position of the entity."""
        self.pos.icopy(vector)
    def worldToPix(self, coord_conv):
        """Calculate the pixel position of the entity."""
        self.sprite.rect.center = coord_conv.worldToPix(self.pos)
    def onEntityMovedEvent(self, event):
        """An EntityModel has changed position."""
        if event.entity_id == self._entity_id:
            self.setCoords(event.pos)

class AreaView(evtman.SingleListener):
    """Display a portion of the world

    This where the tile map is displayed, along with the entities, treasures,
    exploding particle effects, text over the characters' heads...  Your most
    direct view on the world landscape.

    """
    def __init__(self, event_manager, size):
        evtman.SingleListener.__init__(self, event_manager)
        # This view is sensitive to one area only.
        self._area_id = None # No area at all for now.
        # It owns the EntityViews.
        self._entities = {}
        # Entities have sprites that are added to this group for display
        # purposes.
        self._entities_group = pygame.sprite.Group()
        # The information about the floor is stored in tiles:
        self._tilemap = {}
        self._visible_tiles_region = pygame.Rect((0, 0), (0, 0))
        # We need something to convert world coordinates (in meters) to
        # screen coordinates (in pixels).
        self._coord_conv = CoordinatesConverter()
        self._coord_conv.setRefPix((size[0] // 2, size[1] // 2))
        # The view is centered on that entity.  If None, then it's left where
        # it is.
        self._follow_entity_id = None
        # The area view displays the landscape, objects, entities, etc..
        self.sprite = None
        self.createSprite(size)
        #
        # There should be a pygame window open by now, so pygame knows which
        # format is better for the tile images.  Creating them now !
        global TILE_IMAGES_LOW, TILE_IMAGES_HIGH
        TILE_IMAGES_LOW = makeTileImages(0)
        TILE_IMAGES_HIGH = makeTileImages(1)
    def createSprite(self, size):
        """Instantiate the sprite, its image and its rect."""
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        # Too many positional arguments for function call.
        # Somehow pylint is confused by Surface.
        self.sprite.image = pygame.Surface(size)
        # pylint: enable-msg=E1121
        rect = self.sprite.image.get_rect()
        self.sprite.rect = rect
        self._visible_tiles_region.size = size
    def createEntityView(self, entity_id):
        """Create a new view to display an entity of the world."""
        entity_view = EntityView(self._event_manager, entity_id)
        self._entities_group.add(entity_view.sprite)
        self._entities[entity_id] = entity_view
        return entity_view
    def createEntityViewFromSummary(self, summary):
        """Create a new view to display an entity of the world."""
        entity_view = EntityView.fromSummary(self._event_manager, summary)
        self._entities_group.add(entity_view.sprite)
        self._entities[summary['entity_id']] = entity_view
        return entity_view
    def destroyEntityView(self, entity_id):
        """Remove an entity view to stop displaying an entity of the world.

        Note that it does not mean that the entity is not in the world anymore.
        It just means it is not shown.  Out of view, for instance.  Although
        this is not implemented yet.

        """
        entity_view = self._entities.pop(entity_id)
        entity_view.unregister()
        self._entities_group.remove(entity_view.sprite)
    def setAreaId(self, area_id):
        """Select the area that we want to display."""
        if area_id == self._area_id:
            return
        # Empty everything.
        for entity_id in self._entities.keys():
            self.destroyEntityView(entity_id)
        # Ask for new stuff.
        self._area_id = area_id
        self.post(world.events.AreaContentRequest(area_id))
    def renderTiles(self):
        """Displays the tiles."""
        # We do not want to process ALL the tiles of the tile map.  So we look
        # for those that have coordinates matching our view.
        # I did try other methods:
        # * Blit everything, hoping that pygame is smart enough to do nothing
        #   when there is nothing to do: good result on 32*32 maps.
        # * Test for the intersection of the tile rect with the view rect:
        #   horrible all the time.
        # And of course it dit not scale well at all, a 128*128 map was
        # bringing me down to 5 FPS.  So we do not look at all the tiles
        # anymore, we prune.
        size = self._visible_tiles_region.size
        # The weird mix of max and min is due to the fact that the y axis
        # is reversed on the display.
        x_min, y_max = self._coord_conv.pixToWorld((0, 0))
        x_max, y_min = self._coord_conv.pixToWorld(size)
        x_min = int(math.floor(x_min))
        y_min = int(math.floor(y_min))
        x_max = int(math.ceil(x_max))
        y_max = int(math.ceil(y_max))
        tile_rect = pygame.Rect((0, 0), (32, 32))
        image = self.sprite.image
        for y in xrange(y_min, y_max + 1):
            for x in xrange(x_min, x_max + 1):
                try:
                    tile = self._tilemap[(x, y)]
                except KeyError:
                    pass
                else:
                    pos = self._coord_conv.worldToPix(geometry.Vector(x, y))
                    tile_rect.center = pos
                    if tile[1]:
                        tile_image = TILE_IMAGES_HIGH
                    else:
                        tile_image = TILE_IMAGES_LOW
                    tile_image = tile_image[tile[0]] # 0: nature.
                    image.blit(tile_image, tile_rect)

    def render(self):
        """Draw the landscape, the characters, etc.."""
        image = self.sprite.image
        image.fill((64, 64, 64))
        if self._area_id is None:
            return
        # Center the view.
        if self._follow_entity_id is not None:
            try:
                entity = self._entities[self._follow_entity_id]
            except KeyError:
                pass # We just leave the converter where it is.
            else:
                self._coord_conv.setRefWorld(entity.pos)
        # Tile map.
        self.renderTiles()
        # Entities.
        for entity in self._entities.itervalues():
            entity.worldToPix(self._coord_conv)
            entity.render()
        self._entities_group.draw(image)
    def setFollowEntity(self, entity_id):
        """Center the view on that entity."""
        self._follow_entity_id = entity_id
    def onEntityDestroyedEvent(self, event):
        """An entity was removed from the world."""
        if event.entity_id in self._entities:
            self.destroyEntityView(event.entity_id)
    def onEntityEnteredAreaEvent(self, event):
        """An entity entered an area."""
        if event.area_id == self._area_id:
            entity_view = self.createEntityView(event.entity_id)
            entity_view.setCoords(event.pos)
    def onEntityLeftAreaEvent(self, event):
        """An entity left an area."""
        if event.area_id == self._area_id:
            self.destroyEntityView(event.entity_id)
    def onAreaContentEvent(self, event):
        """We were sent a list of what we should display."""
        if event.area_id == self._area_id:
            for summary in event.entities:
                self.createEntityViewFromSummary(summary)
            self._tilemap = event.tilemap
    def onViewAreaEvent(self, event):
        """We are looking at a new area."""
        self.setAreaId(event.area_id)
    def onControlEntityEvent(self, event):
        """A new entity is controlled."""
        self.setFollowEntity(event.entity_id)
