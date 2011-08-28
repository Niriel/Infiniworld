#! /usr/bin/python
"""

"""
import pygame
from infiniworld import evtman
import world
import pygame_

#-------------------------------  GUI widgets.  -------------------------------

class HealthView(evtman.SingleListener):
    """Widget displaying your health."""
    PIC_NAME = 'sprite_heart.png'
    def __init__(self, event_manager):
        self._dirty = True
        evtman.SingleListener.__init__(self, event_manager)
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        # Too many positional arguments for function call
        # Dunno why pylint always complains about Surface.
        self.sprite.image = pygame.Surface((96, 18 * 2))
        # pylint: enable-msg=E1121

        # About the size of the surface: we hardcoded the fact that a bunny has
        # a max of 10 healt points.  We display them on two lines of 5 hearts.
        # The hearts are 16*16 pixels, and we put a border around so we reserve
        # 18*18 for them.

        self.sprite.rect = self.sprite.image.get_rect()
        self.entity_id = None
        self.health = 0
    def render(self, unused):
        """Displays hearts."""
        if not self._dirty:
            return
        image = self.sprite.image
        image.fill((32, 32, 32))
        heart_pic = pygame_.ASSETS_PICS[self.PIC_NAME]
        for heart_id in xrange(1, self.health + 1):
            # Five hearts by row.
            y, x = divmod(heart_id - 1, 5)
            image.blit(heart_pic, (x * 18 + 4, y * 18))
    def setHealth(self, health):
        """Set the number of hearts we must display."""
        self.health = health
        self._dirty = True
        self.render(None)
    def onControlEntityEvent(self, event):
        """A new entity is controlled."""
        self.entity_id = event.entity_id
        self.post(world.HealthRequest(self.entity_id))
    def onHealthEvent(self, event):
        """Someone got hurt or healed."""
        if event.entity_id == self.entity_id:
            self.setHealth(event.amount)

class CarrotCounterView(evtman.SingleListener):
    """Widget Displaying the number of carrots you have in your 'pockets'."""
    PIC_NAME = 'sprite_carrot.png'
    FONT_NAME = 'pf_tempesta_seven.ttf_16'
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._dirty = True
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        # Too many positional arguments for function call
        # Dunno why pylint always complains about Surface.
        self.sprite.image = pygame.Surface((96, 32))
        # pylint: enable-msg=E1121
        self.sprite.rect = self.sprite.image.get_rect()
        self._carrots = 0
    def setCarrots(self, carrots):
        """Sets the number of carrots."""
        self._carrots = carrots
        self._dirty = True
        self.render(None)
    def render(self, unused):
        """Display the widget."""
        if not self._dirty:
            return
        image = self.sprite.image
        image.fill((32, 32, 32))
        carrot_pic = pygame_.ASSETS_PICS[self.PIC_NAME]
        image.blit(carrot_pic, (0, 0))
        font = pygame_.ASSETS_FONTS[self.FONT_NAME]
        height = font.get_height()
        pos_y = (32 - height) // 2
        # Unicode character 00D7 corresponds to the multiplication sign.
        text = font.render(u"\u00d7 %i" % self._carrots, False,
                           (255, 255, 255))
        image.blit(text, (32, pos_y))
    def onCarrotEvent(self, event):
        """Bunny picked up or ate a carrot."""
        # Obviously we should be paying attention to one entity only but fuck
        # it, we KNOW that there is only one bunny here.
        self.setCarrots(event.amount)

class StatusTextView(evtman.SingleListener):
    """Widget for displaying text."""
    DECAY_DURATION = 1 # seconds.
    FONT_NAME = 'pf_tempesta_seven.ttf_16'
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._text = ''
        self._decay_time = 0
        self._decay = 1
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        # Too many positional arguments for function call
        # Dunno why pylint always complains about Surface.
        self.sprite.image = pygame.Surface((800 - 32, 32))
        # pylint: enable-msg=E1121
        self.sprite.rect = self.sprite.image.get_rect()
        self._font = pygame_.ASSETS_FONTS[self.FONT_NAME]
        self._font_height = self._font.get_height()
        self._dirty = True
    def render(self, unused):
        if not self._dirty:
            return
        image = self.sprite.image
        image.fill((32, 32, 32))

        pos_y = (32 - self._font_height) // 2
        alpha = 255 * self._decay
        text = self._font.render(self._text, False, (255, 255, 255, alpha))
        text.set_alpha(alpha)
        image.blit(text, (16, pos_y))
    def setText(self, text):
        self._text = text
        self._decay_time = 0
        self._decay = 1
        self._dirty = True
    def onStatusTextEvent(self, event):
        self.setText(event.text)
    def onRunPhysicsEvent(self, event):
        if self._decay == 0:
            return
        self._decay_time += event.timestep
        self._decay = (self.DECAY_DURATION - self._decay_time) / self.DECAY_DURATION
        if self._decay < 0:
            self._decay = 0
        self._dirty = True

class TimeSpentView(evtman.SingleListener):
    FONT_NAME = 'pf_tempesta_seven.ttf_16'
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._time = 0
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        # Too many positional arguments for function call
        # Dunno why pylint always complains about Surface.
        self.sprite.image = pygame.Surface((96, 32))
        # pylint: enable-msg=E1121
        self.sprite.rect = self.sprite.image.get_rect()
        self._font = pygame_.ASSETS_FONTS[self.FONT_NAME]
        self._font_height = self._font.get_height()
        self._dirty = True
        self._frozen = False
    def render(self, unused):
        if not self._dirty:
            return
        image = self.sprite.image
        image.fill((32, 32, 32))

        minutes, seconds = divmod(self._time, 60)
        text = "%3i:%05.2f" % (minutes, seconds)

        pos_y = (32 - self._font_height) // 2
        text = self._font.render(text, False, (255, 255, 255))
        image.blit(text, (0, pos_y))
    def onRunPhysicsEvent(self, event):
        if not self._frozen:
            self._time += event.timestep
            self._dirty = True
    def onGameOverEvent(self, unused):
        self._frozen = True

class StatsView(evtman.SingleListener):
    FONT_NAME = 'pf_tempesta_seven.ttf_16'
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        self.sprite.image = pygame.Surface((96, 64))
        self.sprite.rect = self.sprite.image.get_rect()
        self._dirty = True
        #
        self._font = pygame_.ASSETS_FONTS[self.FONT_NAME]
        self._font_height = self._font.get_height()
        #
        self._living_foxes = 0
        self._dead_foxes = 0
    def render(self, unused):
        if not self._dirty:
            return
        self._dirty = False
        image = self.sprite.image
        image.fill((32, 32, 32))
        pics = (pygame_.ASSETS_PICS['sprite_fox.png'],
                pygame_.ASSETS_PICS['sprite_blood.png'])
        numbers = (self._living_foxes,
                   self._dead_foxes)
        stats = zip(pics, numbers)
        color = (255, 255, 255)
        for stat_id, (pic, number) in enumerate(stats):
            text = self._font.render(u"\u00d7 %i" % number, False, color)
            image.blit(pic, (0, stat_id * 32))
            image.blit(text, (32, stat_id * 32 + 16 - self._font_height // 2))
    def onEntityEnteredAreaEvent(self, event):
        if event.entity_summary['name'] == 'Zombie fox':
            self._living_foxes += 1
            self._dirty = True
    def onCreatureDiedEvent(self, event):
        if event.entity_id != 0:
            # Here we KNOW that entity id 0 is for the bunny and that all the
            # others are foxes.
            self._living_foxes -= 1
            self._dead_foxes += 1
            self._dirty = True


#---------------------------------  Entities.  --------------------------------

class MyEntityView(pygame_.EntityView):
    """Our entities all have a single sprite in the assets list."""
    PIC_NAME = None # Just to break stuff.
    def __init__(self, event_manager, entity_id):
        self._original_image = pygame_.ASSETS_PICS[self.PIC_NAME]
        pygame_.EntityView.__init__(self, event_manager, entity_id)
    def createSprite(self):
        pygame_.EntityView.createSprite(self)
        self.sprite.image = self._original_image
    def render(self):
        pass

class CreatureView(MyEntityView):
    """Base view for creatures."""
    OWN_IMAGE = True
    CORPSE = 'Blood'
    DAMAGE_COOLDOWN = .5
    def __init__(self, event_manager, entity_id):
        MyEntityView.__init__(self, event_manager, entity_id)
        self._damage_time = 0
        self._hurt = False
        # pylint: disable-msg=E1121
        self._hurt_surface = pygame.Surface((32, 32))
    def render(self):
        """Displays us, with a red hue if we're hurt."""
        if not self._dirty:
            return
        self._dirty = False
        if self._hurt:
            image = self._original_image.copy()
            intensity = int(255 * self._damage_time / self.DAMAGE_COOLDOWN)
            # We become red by removing the blue and the green from our sprite.
            self._hurt_surface.fill((0, intensity, intensity))
            image.blit(self._hurt_surface, (0, 0), None, pygame.BLEND_RGB_SUB)
            self.sprite.image = image
        else:
            self.sprite.image = self._original_image
    def leaveCorpse(self):
        """Special effect when creature dies."""
        factory = pygame_.ENTITY_VIEW_FACTORIES[self.CORPSE]
        corpse = self.area_view.createSfxEntityView(factory)
        corpse.old_pos = self.new_pos
        corpse.new_pos = self.new_pos
    def onCreatureDiedEvent(self, event):
        """We're dead: leave a corpse behind."""
        if event.entity_id == self._entity_id:
            self.leaveCorpse()
    def onAttackEvent(self, event):
        """We're under attack: become red for a little while."""
        if event.victim == self._entity_id:
            self._hurt = True
            self._damage_time = self.DAMAGE_COOLDOWN
            self._dirty = True
    def onRunPhysicsEvent(self, event):
        """Time flows: update our red appearance if we're hurt."""
        if self._hurt:
            self._damage_time -= event.timestep
            if self._damage_time <= 0:
                self._damage_time = 0
                self._hurt = False
            self._dirty = True

class BunnyView(CreatureView):
    """We're cute."""
    PIC_NAME = 'sprite_bunny.png'
    CORPSE = 'Dead bunny'
    SPRITE_OFFSET = (0, -5)
    def createShockWave(self):
        """Generate special effect around us."""
        shockwave_view = self.area_view.createSfxEntityView(ShockWaveView)
        shockwave_view.old_pos = self.new_pos
        shockwave_view.new_pos = self.new_pos
    def onShockWaveEvent(self, event):
        """Bunny uses super psy powers."""
        if event.entity_id == self._entity_id:
            self.createShockWave()

class ZombieFoxView(CreatureView):
    """This is what your enemy looks like."""
    PIC_NAME = 'sprite_fox.png'

class CarrotView(MyEntityView):
    """Your food."""
    PIC_NAME = 'sprite_carrot.png'

#-----------------------------  Special effects.  -----------------------------

class BloodView(MyEntityView):
    """For dead foxes."""
    PIC_NAME = 'sprite_blood.png'
    LAYER = pygame_.LAYER_LOW

class DeadBunnyView(MyEntityView):
    """So sad."""
    PIC_NAME = 'sprite_bunny_dead.png'
    LAYER = pygame_.LAYER_LOW

class ShockWaveView(pygame_.EntityView):
    """Animated telekynetic shock wave."""
    LAYER = pygame_.LAYER_HIG
    RADIUS = 10 * 32 # pixels.
    DURATION = .5 # s
    SPEED = RADIUS / DURATION
    def __init__(self, event_manager, entity_id):
        pygame_.EntityView.__init__(self, event_manager, entity_id)
        self._age = 0
        self._radius = 0
        width = self.RADIUS * 2 + 1
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        self.sprite.image = pygame.Surface((width, width), pygame.SRCALPHA)
        self.sprite.rect = self.sprite.image.get_rect()
        self._center = self.sprite.rect.center
        self._dirty = True
    def render(self):
        if not self._dirty:
            return
        image = self.sprite.image
        image.fill((0, 0, 0, 0))
        alpha = 255 * (1 - self._age / self.DURATION)
        pygame.draw.circle(image, (220, 220, 255, alpha), self._center,
                           int(self._radius))
    def onRunPhysicsEvent(self, event):
        """Propagates the wave."""
        self._age += event.timestep
        if self._age > self.DURATION:
            self.area_view.destroyEntityView(self._entity_id)
        else:
            self._radius = self._age * self.SPEED
            self._dirty = True

def setupEntityViewFactories():
    """Tell pygame_ which EntityView correspond to an EntityModel's name."""
    factories = {'Bunny' : BunnyView,
                 'Zombie fox' : ZombieFoxView,
                 'Carrot' : CarrotView,
                 'Blood' : BloodView,
                 'Dead bunny' : DeadBunnyView}
    pygame_.ENTITY_VIEW_FACTORIES.update(factories)


class StartScreenView(evtman.SingleListener):
    """Press [space] to start."""
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._dirty = True
        self.sprite = pygame.sprite.Sprite()
    def render(self, unused):
        if not self._dirty:
            return
        self._dirty = True
        self.sprite.rect = pygame.display.get_surface().get_rect()
        # pylint: disable-msg=E1121
        # Too many positional arguments.  Pylint doesn't like Surface
        # for some reason.
        self.sprite.image = pygame.Surface(self.sprite.rect.size)
        # pylint: enable-msg=E1121
        image = self.sprite.image
        image.fill((0, 163, 71))
        #
        font = pygame.font.Font(None, 92)
        text = font.render(u"Apocalypse Bunny.", True, (200, 200, 200))
        text_rect = text.get_rect()
        text_rect.center = (400, 100)
        image.blit(text, text_rect)
        #
        font = pygame.font.Font(None, 32)
        font_height = font.get_height()
        lines = ["WASD keys to move.",
                 "Avoid the zombie foxes.",
                 "Pick up the radioactive carrots.",
                 "Radioactive carrots give you a superpower:",
                 "Press [space] to blast foxes with a psy-wave.",
                 "Use your carrots wisely!",
                 "Survive as long as you can.",
                 "Press [m] to take a screen shot.",
                 "Press [p] to pause and [Esc] to quit."]
        for y, line in enumerate(lines):
            text = font.render(line, True, (200, 200, 200))
            text_rect = text.get_rect()
            text_rect.center = (400, 175 + y * font_height)
            image.blit(text, text_rect)
        #
        font = pygame.font.Font(None, 48)
        text = font.render(u"Press [space] to start.", True, (200, 200, 200))
        text_rect = text.get_rect()
        text_rect.center = (400, 420)
        image.blit(text, text_rect)

class GameOverScreenView(evtman.SingleListener):
    """Overlays a game over message on the main screen."""
    def __init__(self, event_manager, time):
        evtman.SingleListener.__init__(self, event_manager)
        self._dirty = True
        self._time = time
        self.sprite = pygame.sprite.Sprite()
        # pylint: disable-msg=E1121
        self.sprite.image = pygame.Surface(pygame.display.
                                           get_surface().get_rect().size,
                                           pygame.SRCALPHA)
        self.sprite.rect = self.sprite.image.get_rect()
    def render(self, unused):
        """Game over text."""
        if not self._dirty:
            return
        self._dirty = False
        #
        self.sprite.image.fill((0, 0, 0, 64))
        #
        font = pygame.font.Font(None, 92)
        text = font.render(u"Awww, poor bunny!", True, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.center = (400, 100)
        self.sprite.image.blit(text, text_rect)
        #
        font = pygame.font.Font(None, 64)
        text = u"You survived for"
        text = font.render(text, True, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.center = (400, 300)
        self.sprite.image.blit(text, text_rect)
        #
        minutes, seconds = divmod(self._time, 60)
        if minutes == 0:
            time = u""
        elif minutes == 1:
            time = u"1 minute and "
        else:
            time = u"%i minutes and " % minutes
        if seconds < 2:
            time += u"%05.2f second" % seconds
        else:
            time += u"%05.2f seconds" % seconds
        text = time + u"."
        text = font.render(text, True, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.center = (400, 350)
        self.sprite.image.blit(text, text_rect)

