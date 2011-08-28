"""Code that is specific to pygame."""

# The calls to pygame.Surface() are all surrounded by a Pylint command asking
# Pylint to stop complaining about the parameters.  I don't know why pylint
# freaks out with that call.

# Standard library.
from __future__ import division
import logging
import math
import os
import time # For naming screenshots.
import weakref
# Non standard libraries.
import pygame
# My stuff.
import directories
from infiniworld import controllers
from infiniworld import events
from infiniworld import evtman
from infiniworld import geometry
from infiniworld import models

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
# pylint: enable-msg=R0903

class FPSSprite(pygame.sprite.Sprite):
    """Sprite that displays the number of frames per second."""
    # The implementation is a bit weird, it uses the pygame (SDL) clock which I
    # use nowhere else.  But that's okay.
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)
        self.image = None
        self.rect = None
        self._pos = pos
        self._clock = pygame.time.Clock()
        self._font = pygame.font.Font(None, 24)
        self._old_fps = -1
    def update(self):
        """Use the pygame clock to get the FPS and makes an image for it."""
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

#---------------------------------  Assets.  ---------------------------------

ASSETS_PICS = {} # This contains ALL the pictures for the game.
ASSETS_FONTS = {} # And this contains all the fonts.
# These dictionaries have strings as keys and pygame surfaces or fonts as
# values.  They are filled with the loadPictures and loadFonts functions below.
# Although, they are not filled directly, nor here.  It's the job of your game
# to load the files and put them in those dictionaries.

def loadPictures(file_names):
    """Load a bunch of pictures and return them in a dictionary.

    The keys of the dictionary are the file names, the values are pygame
    surfaces.

    This function uses the directories module to find where the images are
    stored.

    This function does not assume that the pygame display is already active.
    Having a pygame display active is required for convert to work. You have to
    apply Surface.convert or Surface.convert_alpha yourself.  These methods
    modify the picture format for fast blitting on the display.

    """
    directory = directories.DIR_SHARE
    pics = {}
    for file_name in file_names:
        path = os.path.join(directory, file_name)
        LOGGER.debug('Loading image %s', path)
        picture = pygame.image.load(path)
        pics[file_name] = picture
    return pics

def loadFonts(file_names_and_sizes):
    """Load a bunch of fonts and return them in a dictionary.

    Use it like that:

    fonts = loadFonts([('Arial', 12), ('Arial', 16), ('Times', 16)])

    The keys of the dictionary are a mangling of the file names and the sizes
    (for example 'Arial_16'), the values are pygame fonts.

    This function uses the directories module to find where the fonts are
    stored.

    The pygame font module must be initialized, so the fonts are loaded after
    pygame is initialized.

    """
    directory = directories.DIR_SHARE
    fonts = {}
    for file_name, size in file_names_and_sizes:
        path = os.path.join(directory, file_name)
        LOGGER.debug('Loading font %s', path)
        font = pygame.font.Font(path, size)
        fonts['%s_%i' % (file_name, size)] = font
    return fonts

#----------------------------------  Tiles.  ----------------------------------

# Tiles exist in two versions: low (floor-like) and high (wall-like).

# These dictionaries map a file name to a tile nature.
TILE_ASSETS_LOW = {}
TILE_ASSETS_HIGH = {}
# And these map a pygame surface to a tile nature.
TILE_IMAGES_LOW = {}
TILE_IMAGES_HIGH = {}
# I am aware that those names are confusing...  I'll work on it.

def makeTileImages(elevation):
    """Generate beautiful bitmaps for displaying sprites."""

    def draw3dBorder(image, color, thickness):
        """Welcome back to the 90s!

        `color` must be a (r, g, b) or (r, g, b, a) tuple.

        I wish you could give Color.__init__ a Color object as argument to make a
        copy or to stop worrying about types.  But no :(.

        This function is used to draw high tiles when there is no art for it.  It's
        crude but it does the job.  It is called by makeTileImages.

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

    size = (32, 32)
    # These colors are used only if there is no asset for a given tile.
    # From http://hyperphysics.phy-astr.gsu.edu/hbase/vision/cie.html
    colors = {models.tile.NATURE_DEEPWATER: (92, 138, 202),
              models.tile.NATURE_DIRT: (152, 118, 84),
              models.tile.NATURE_GRASS: (0, 163, 71),
              models.tile.NATURE_RUBBER: (32, 32, 32),
              models.tile.NATURE_SAND: (234, 231, 94),
              models.tile.NATURE_SHALLOWWATER: (110, 175, 199),
              models.tile.NATURE_STONE: (128, 128, 128)}
    images = {}
    tile_asset = (TILE_ASSETS_LOW, TILE_ASSETS_HIGH)[elevation]
    for nature, color in colors.iteritems():
        # pylint: disable-msg=E1121
        if nature in tile_asset:
            asset_name = tile_asset[nature]
            image = ASSETS_PICS[asset_name]
        else:
            image = pygame.Surface(size)
            image.fill(color)
            if elevation == 1:
                draw3dBorder(image, color, 4)
        # pylint: enable-msg=E1121
        images[nature] = image
    return images

#----------------------  pygame (SDL) events controller  ----------------------

# IMPORTANT: we are dealing with two sorts of events here.
# * evtman.Event which we implemented ourselves.  They are used by our models
#   views and controllers to talk to each other.
# * SDL events.  They are a totally different kind of events generated by
#   SDL.  They correspond to mouse clicks, key presses, windows iconification,
#   etc.
# The PygameController translates SDL events into evtman.Event objects.
class PygameController(evtman.SingleListener):
    """Reads the input from the keyboard and mouse from pygame."""
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._old_pressed = set()

    def _scanKeyboard(self):
        """Look at what keys are actually pressed, and reacts."""
        # I found out that only looking at the KEYUP and KEYDOWN events was not
        # reliable.
        #
        # 1) These events are not created if the key was pushed or released
        # when the pygame window wasn't focused.  It is possible that some
        # application suddenly pops up and steal the keyboard focus, and then
        # you release your 'North' key but the game does not realize, and when
        # you go back to it you have to press and re-release North.  It sucks.
        #
        # 2) If you have dead keys, which is common when you use an
        # international keyboard layout, the KeyDown events are not triggered
        # immediately.  This makes KeyUp and KeyDown nice for entering text
        # but bad for controlling a character on the screen.
        #
        # This has limits too unfortunately.  Buttons like NumLock are
        # considered pressed even when they're not, as long as they are
        # 'active'.  Same for the Pause/Break key I wanted to use for pausing
        # the game: that key self-releases as soon as you push it, for some
        # reason.  That prevents you to actually detect it because the current
        # function is not good enough.  For such keys, the KeyDown event may
        # be more appropriate.
        pressed = pygame.key.get_pressed()
        new_pressed = set((key
                           for key in xrange(len(pressed))
                           if pressed[key]))
        keys_down = new_pressed - self._old_pressed
        keys_up = self._old_pressed - new_pressed
        for key in keys_up:
            self.post(controllers.keyboard.KeyUpEvent(key))
        for key in keys_down:
            self.post(controllers.keyboard.KeyDownEvent(key))
        self._old_pressed = new_pressed


    def _keyDown(self, pygame_event):
        """Process pygame KEYDOWN events."""
        # The KeyDown event is very good to let the user enter text. We could
        # also use it for weird keys like Pause.
        char = pygame_event.unicode
        if char:
            self.post(controllers.keyboard.LetterTypedEvent(unicode))

    def pumpPygameEvents(self):
        """Process the events sent by pygame.

        It's best to call that very often to make sure that the application
        remains responsive.

        """
        for pygame_event in pygame.event.get():
            pygame_event_type = pygame_event.type
            if pygame_event_type == pygame.QUIT:
                self.post(events.QuitEvent())
            elif pygame_event_type == pygame.KEYDOWN:
                self._keyDown(pygame_event)
        self._scanKeyboard()

    def onProcessInputsEvent(self, unused):
        """The main loop asks for inputs."""
        self.pumpPygameEvents()

#-----------------------  The main View using pygame.  ------------------------

class PygameView(evtman.SingleListener):
    """The root of everything that's going to be on screen."""
    def __init__(self, event_manager, title, resolution):
        evtman.SingleListener.__init__(self, event_manager)
        # For some reason, on Ubuntu 11.04, I cannot change the caption of the
        # window once it is created, only the caption in the task bar is
        # modified if I call set_caption after set_mode.  So I set the caption
        # first and then I create the game window.
        pygame.display.set_caption(title)
        self._surface = pygame.display.set_mode(resolution)
        # PyGame view contains other views.  See it as a window containing
        # several widgets.  Our widgets are horribly primitive for now.
        self._views = set()
        # This is how we draw the widgets on the screen.  Here again, this is
        # barely good enough for now.
        self._group = pygame.sprite.OrderedUpdates()
        # The FPS sprite is not a view, just a sprite, so we put it in there.
        fps_sprite = FPSSprite((0, 0))
        self._group.add(fps_sprite)
    def addView(self, view):
        """Tell PygameView to display the given view."""
        self._views.add(view)
        self._group.add(view.sprite)
    def removeView(self, view):
        """Tell PygameView to stop displaying the given view."""
        self._views.remove(view)
        self._group.remove(view.sprite)
    def render(self, ratio):
        """Display things on screen."""
        self._surface.fill((0, 0, 0))
        for view in self._views:
            view.render(ratio)
        self._group.update()
        self._group.draw(self._surface)
        pygame.display.flip()
    def takeScreenShot(self):
        """Save the screen in a PNG file."""
        now = time.localtime()
        suffix = 0
        while True:
            file_name = "%i-%02i-%02i_%02i-%02i-%02i-%i.png" % (now.tm_year,
                                                                now.tm_mon,
                                                                now.tm_mday,
                                                                now.tm_hour,
                                                                now.tm_min,
                                                                now.tm_sec,
                                                                suffix)
            path = os.path.join(directories.DIR_VAR_SCR, file_name)
            if os.path.exists(path):
                suffix += 1
            else:
                pygame.image.save(self._surface, path)
                LOGGER.info("Screenshot: %s", file_name)
                self.post(events.StatusTextEvent("Screenshot: %s." % file_name))
                break
    def onRenderFrameEvent(self, event):
        """The game loop asks us to draw something."""
        self.render(event.ratio)
    def onScreenShotCommand(self, unused):
        self.takeScreenShot()


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


#------------------------------  Entity Views.  ------------------------------

LAYER_LOW = 0 # Blood stains on the floor.
LAYER_MID = 1 # Normal creatures.
LAYER_HIG = 2 # Birds, some special effects.

class EntityView(evtman.SingleListener):
    """Managed the appearance of an entity on screen."""
    SPRITE_SIZE = (32, 32)
    SPRITE_OFFSET = (0, 0)
    LAYER = LAYER_MID
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
        # EntityViews hold a weak reference to their AreaView.  This allows
        # them to create new EntityView such as special effects.
        self._area_view = None
        # World coordinates.  The apparent position is interpolated between
        # these two positions.
        self.old_pos = geometry.Vector()
        self.new_pos = geometry.Vector()
        self.int_pos = geometry.Vector() # The interpolated one.
        #
        self.sprite = None
        self.createSprite()
        self._dirty = True

    def _getAreaView(self):
        """Return the AreaView on which this EntityView is displayed."""
        if self._area_view is None:
            return None
        return self._area_view()
    def _setAreaView(self, value):
        """Tell the EntityView that it is displayed by the given AreaView."""
        if value is None:
            self._area_view = None
        else:
            self._area_view = weakref.ref(value)
    area_view = property(_getAreaView, _setAreaView, None,
                         "AreaView displaying this EntityView.")

    def applySummary(self, summary):
        """Configure the view using the info from the summary."""
        if summary['entity_id'] != self._entity_id:
            raise ValueError("entity_id mismatch")
        pos = summary['pos']
        self.old_pos = pos
        self.new_pos = pos
    def createSprite(self):
        """Instantiate the sprite, its image and its rect."""
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        # Too many positional arguments for function call.
        # Somehow pylint is confused by Surface.
        self.sprite.image = pygame.Surface(self.SPRITE_SIZE, pygame.SRCALPHA)
        # pylint: enable-msg=E1121
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
        """Set the new world position of the entity."""
        self.old_pos = self.new_pos
        self.new_pos = vector
    def interpolatePosition(self, ratio):
        """Compute where the entity should be now.

        We render the frames more often than we update the physics.  There
        is a need for interpolation.

        We do a simple linear interpolation between the last two known physics
        states.

        This means that we are always showing something that is a little bit in
        the past.  That's okay, we are talking about a small fraction of a
        second here.

        """
        # It is important to store the interpolated position on the object
        # because it is used by the AreaView to center itself.
        self.int_pos = (self.old_pos * (1 - ratio) +
                        self.new_pos * ratio)
        # Also, we compute a*(1-r) + b*r and NOT a+r*(b-a) because that second
        # possibility, although mathematically equivalent, introduces numerical
        # rounding errors and therefore does NOT ensure that you end up in b.
    def worldToPix(self, coord_conv):
        """Move the sprite to the pixel position corresponding to its world
        position."""
        self.sprite.rect.center = coord_conv.worldToPix(self.int_pos)
        self.sprite.rect.move_ip(self.SPRITE_OFFSET)
        return self.sprite.rect.center
    def onEntityMovedEvent(self, event):
        """An EntityModel has changed position."""
        if event.entity_id == self._entity_id:
            self.setCoords(event.pos)
    def onEntityStoppedEvent(self, event):
        """An EntityModel has changed position."""
        if event.entity_id == self._entity_id:
            # This overwrites the old pos, making both positions identical and
            # therefore the interpolation also yields new_pos.  If you don't do
            # that, once an entity stops moving, it keeps spazing between its
            # last two positions.
            self.setCoords(self.new_pos)


ENTITY_VIEW_FACTORIES = {'Entity': EntityView}


#--------------------------------  Area View  --------------------------------

class AreaView(evtman.SingleListener):
    """Display a portion of the world

    This where the tile map is displayed, along with the entities, treasures,
    exploding particle effects, text over the characters' heads...  Your most
    direct view on the world landscape.

    """
    def __init__(self, event_manager, size):
        evtman.SingleListener.__init__(self, event_manager)
        # This view is sensitive to one area only.
        self.area_id = None # No area at all for now.
        # It owns the EntityViews.
        self.entities = {}
        # Entities have sprites that are added to this group for display
        # purposes.
        self._entities_bottom_group = pygame.sprite.LayeredUpdates()
        self._entities_mid_group = pygame.sprite.LayeredUpdates()
        self._entities_top_group = pygame.sprite.LayeredUpdates()
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
        # It also displays purely visual effects that don't represent anything
        # from the world model.  These are indicated with a negative entity_id.
        # Indeed, all the model entities have entity_id >= 0.
        self._sfx_id_min = 0
        #
        # There should be a pygame window open by now, so pygame knows which
        # format is better for the tile images.  Creating them now !
        TILE_IMAGES_LOW.update(makeTileImages(0))
        TILE_IMAGES_HIGH.update(makeTileImages(1))
        #
        # When the physics is paused, we write it in big in the middle of the
        # AreaView.  Also, we don't need to do all the complicated rendering
        # so we skip that part.
        self._paused_physics = False
        self._paused_shown = False
    def createSprite(self, size):
        """Instantiate the sprite, its image and its rect."""
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        # Too many positional arguments for function call.
        # Somehow pylint is confused by Surface.
        self.sprite.image = pygame.Surface(size)
        # pylint: enable-msg=E1121
        #
        # Important note: the two rectangles here are different.
        # _visible_tiles_region keeps (0, 0) as origin and is used to check if
        # some features are visible or not.  The other has its origin modified
        # so that the area is displayed wherever on the screen.
        self.sprite.rect = self.sprite.image.get_rect()
        self._visible_tiles_region.size = size
    def createEntityView(self, entity_id, factory):
        """Create a new view to display an entity of the world."""
        # There is no need to add the entity sprite to a sprite group at this
        # stage: the rendering takes care of it.
        entity_view = factory(self._event_manager, entity_id)
        self.entities[entity_id] = entity_view
        entity_view.area_view = self
        return entity_view
    def createSfxEntityView(self, factory):
        """Create a new view for special effects."""
        self._sfx_id_min -= 1
        return self.createEntityView(self._sfx_id_min, factory)
    def createEntityViewFromSummary(self, summary):
        """Create a new view to display an entity of the world."""
        name = summary['name']
        factory = ENTITY_VIEW_FACTORIES[name]
        entity_view = factory.fromSummary(self._event_manager, summary)
        self._entities_mid_group.add(entity_view.sprite)
        self.entities[summary['entity_id']] = entity_view
        entity_view.area_view = self
        return entity_view
    def destroyEntityView(self, entity_id):
        """Remove an entity view to stop displaying an entity of the world.

        Note that it does not mean that the entity is not in the world anymore.
        It just means it is not shown.  Out of view, for instance.  Although
        this is not implemented yet.

        """
        entity_view = self.entities.pop(entity_id)
        entity_view.area_view = None
        entity_view.unregister()
    def setAreaId(self, area_id):
        """Select the area that we want to display."""
        if area_id == self.area_id:
            return
        # Empty everything.
        for entity_id in self.entities.keys():
            self.destroyEntityView(entity_id)
        self._tilemap.clear()
        self._sfx_id_min = 0
        # Ask for new stuff.
        self.area_id = area_id
        self.post(models.events.AreaContentRequest(area_id))
    def renderTiles(self):
        """Displays the tiles."""
        # We do not want to process ALL the tiles of the tile map.  So we look
        # for those that have coordinates matching our view.
        # I did try other methods:
        # * Blit everything, hoping that pygame is smart enough to do nothing
        #   when there is nothing to do: good result on 32*32 maps.
        # * Test for the intersection of the tile rect with the view rect:
        #   horrible all the time.
        # And of course it did not scale well at all, a 128*128 map was
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

    def renderEntities(self, ratio):
        """Blits the entity sprites on the AreaView sprite."""
        # I don't want to blit ALL the entities of the area, especially if they
        # don't show on the screen.  I did test with 100 entities to display
        # on a 64*64 map, and I ran around for quite some time.

        # This is the perf when I blit EVERYTHING:
        #   ncalls  tottime  percall  cumtime  percall
        #      373    0.196    0.001    2.815    0.008
        # 2.815 / 373 = 0.0075469168900804285

        # So I chose to empty the group and only display what intersects the
        # screen (current implementation):
        #      492    0.204    0.000    2.626    0.005
        # 2.626 / 492 = 0.00533739837398374

        # We do the same work in 70% of the time.  I tried to do better:
        # instead of emptying the entire group and re-add everything, I just
        # remove what is invisible, add what wasn't in yet, and change the
        # layer when it's already here.  It's actually a bit worse:

        # Adding, removing and changing layer:
        #      564    0.302    0.001    3.280    0.006
        # 3.280 / 564 = 0.0058156028368794325

        # We're 10 % above the previous time.  So I went back to the method
        # consisting in emptying everything every time and adding only what
        # I need.
        groups = (self._entities_bottom_group,
                  self._entities_mid_group,
                  self._entities_top_group)
        for group in groups:
            group.empty()
        area_rect = self._visible_tiles_region
        for entity in self.entities.itervalues():
            entity.interpolatePosition(ratio)
            sprite = entity.sprite
            unused, y = entity.worldToPix(self._coord_conv)
            if area_rect.colliderect(sprite.rect):
                entity.render()
                groups[entity.LAYER].add(sprite, layer=y)
        for group in groups:
            group.draw(self.sprite.image)

    def render(self, ratio):
        """Draw the landscape, the characters, etc.."""
        if self._paused_physics:
            if self._paused_shown:
                return
            font = pygame.font.Font(None, 92)
            text_image = font.render("Paused.", True, (255, 255, 255))
            text_rect = text_image.get_rect()
            text_rect.center = self.sprite.image.get_rect().center
            self.sprite.image.blit(text_image, text_rect)
            self._paused_shown = True
            return
        image = self.sprite.image
        image.fill((64, 64, 64))
        if self.area_id is None:
            return
        # Center the view.
        if self._follow_entity_id is not None:
            try:
                entity = self.entities[self._follow_entity_id]
            except KeyError:
                pass # We just leave the converter where it is.
            else:
                entity.interpolatePosition(ratio)
                self._coord_conv.setRefWorld(entity.int_pos)
        # Tile map.
        self.renderTiles()
        # Entities.
        self.renderEntities(ratio)
    def setFollowEntity(self, entity_id):
        """Center the view on that entity."""
        self._follow_entity_id = entity_id
    def pausePhysics(self, paused):
        """Puts the AreaView in paused/unpaused mode."""
        if paused == self._paused_physics:
            return
        self._paused_physics = paused
        self._paused_shown = False
    def onEntityDestroyedEvent(self, event):
        """An entity was removed from the world."""
        if event.entity_id in self.entities:
            self.destroyEntityView(event.entity_id)
    def onEntityEnteredAreaEvent(self, event):
        """An entity entered an area."""
        if event.entity_summary['area_id'] == self.area_id:
            self.createEntityViewFromSummary(event.entity_summary)
    def onEntityLeftAreaEvent(self, event):
        """An entity left an area."""
        if event.area_id == self.area_id:
            self.destroyEntityView(event.entity_id)
    def onAreaContentEvent(self, event):
        """We were sent a list of what we should display."""
        if event.area_id == self.area_id:
            for summary in event.entities:
                self.createEntityViewFromSummary(summary)
            self._tilemap = event.tilemap
    def onViewAreaEvent(self, event):
        """We are looking at a new area."""
        self.setAreaId(event.area_id)
    def onControlEntityEvent(self, event):
        """A new entity is controlled."""
        self.setFollowEntity(event.entity_id)
    def onTogglePausePhysicsCommand(self, unused):
        """Player (un)pauses the game."""
        self.pausePhysics(not self._paused_physics)
    def onPausePhysicsCommand(self, event):
        """Game (un)pauses itself."""
        self.pausePhysics(event.paused)
