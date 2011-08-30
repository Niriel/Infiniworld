#! /usr/bin/python
"""Apocalypse Bunny!

"""
# Standart library.
import logging
# My stuff.
# General.
from infiniworld import events
from infiniworld import evtman
from infiniworld import models
from infiniworld.controllers.player import PlayerController
from infiniworld.controllers.loop import GameLoopController
from controllers.keyboard import StartScreenKeyboardController
from controllers.keyboard import GameScreenKeyboardController
from controllers.keyboard import PauseScreenKeyboardController
from controllers.keyboard import GameOverScreenKeyboardController
# Pygame related.
import pygame_
# Bunny related.
import assets
import gen
import views

LOGGER = logging.getLogger('bunny')

class Game(evtman.SingleListener):
    """Do-it-all class.

    Very dirty because we don't have a decent GUI manager.

    """
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        views.setupEntityViewFactories()
        #
        self._world_model, self._fox_spawner, self._carrot_spawner = gen.GenerateWorld(event_manager, (64, 64))
        self._player_controller = PlayerController(event_manager)
        self._game_loop_controller = GameLoopController(event_manager)
        self._keyboard_controller = StartScreenKeyboardController(event_manager)
        self._area_view = None
        self._time_spent_view = None
        self._health_view = None
        self._carrot_counter_view = None
        self._stats_view = None
        self._status_text_view = None
        self._game_over_view = None
        self._time = 0
        #
        with pygame_.Pygame():
            self._pygame_view = pygame_.PygameView(event_manager,
                                                   u"Apocalypse Bunny", (800, 480))
            assets.load()
            self._title_view = views.StartScreenView(event_manager)
            self._pygame_view.addView(self._title_view)
            self._pygame_controller = pygame_.PygameController(event_manager)
            # Here I select the bunny and show its area.  It's a bit of a hack
            # since I know their entity_id and area_id.  But I don't care, this
            # game is supposed to be quick and dirty.
            # Run the game until a QuitEvent is posted.
            self._game_loop_controller.run()
            LOGGER.info("Stopping...")
    def onStartGameCommand(self, unused):
        self._pygame_view.removeView(self._title_view)
        self._title_view.unregister()
        self._title_view = None
        self._keyboard_controller.unregister()
        self._keyboard_controller = None # Will be set when game is unpaused.
        #
        self._area_view = pygame_.AreaView(self._event_manager, (13 * 32, 13 * 32))
        self._area_view.sprite.rect.midtop = (400, 8)
        self._time_spent_view = views.TimeSpentView(self._event_manager)
        self._time_spent_view.sprite.rect.topleft = (650, 32)
        self._health_view = views.HealthView(self._event_manager)
        self._health_view.sprite.rect.topleft = (650, 96)
        self._carrot_counter_view = views.CarrotCounterView(self._event_manager)
        self._carrot_counter_view.sprite.rect.topleft = (650, 160)
        self._stats_view = views.StatsView(self._event_manager)
        self._stats_view.sprite.rect.topleft = (650, 192)
        self._status_text_view = views.StatusTextView(self._event_manager)
        self._status_text_view.sprite.rect.bottomleft = (16, 480 - 16)
        self._pygame_view.addView(self._area_view)
        self._pygame_view.addView(self._time_spent_view)
        self._pygame_view.addView(self._health_view)
        self._pygame_view.addView(self._stats_view)
        self._pygame_view.addView(self._carrot_counter_view)
        self._pygame_view.addView(self._status_text_view)
        self._keyboard_controller = GameScreenKeyboardController(self._event_manager)
        self.post(models.events.ControlEntityEvent(0))
        self.post(models.events.ViewAreaEvent(0))
        self.post(events.PausePhysicsRequest(False))
    def onGameOverEvent(self, unused):
        self._keyboard_controller.unregister()
        self._game_over_view = views.GameOverScreenView(self._event_manager,
                                                        self._time)
        self._pygame_view.addView(self._game_over_view)
        self._keyboard_controller = GameOverScreenKeyboardController(self._event_manager)
    def onPhysicsPausedEvent(self, event):
        if self._keyboard_controller:
            self._keyboard_controller.unregister()
        if event.paused:
            self._keyboard_controller = PauseScreenKeyboardController(self._event_manager)
        else:
            self._keyboard_controller = GameScreenKeyboardController(self._event_manager)
    def onRunPhysicsEvent(self, event):
        self._time += event.timestep
