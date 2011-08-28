#! /usr/bin/python
"""

"""
from infiniworld.controllers import keyboard as keyboard
from infiniworld import events

class StartScreenKeyboardController(keyboard.KeyboardController):
    def setup(self):
        start_game_event = events.StartGameCommand()
        self.key_down_events[keyboard.K_ESCAPE] = events.QuitEvent()
        self.key_down_events[keyboard.K_RETURN] = start_game_event
        self.key_down_events[keyboard.K_SPACE] = start_game_event
        self.key_down_events[keyboard.K_m] = events.ScreenShotCommand()

class GameScreenKeyboardController(keyboard.KeyboardController):
    def setup(self):
        self.key_down_events[keyboard.K_ESCAPE] = events.QuitEvent()
        self.key_down_events[keyboard.K_SPACE] = events.FireCommand()
        self.key_down_events[keyboard.K_m] = events.ScreenShotCommand()
        self.key_down_events[keyboard.K_p] = events.TogglePausePhysicsCommand()
        self.key_down_events[keyboard.K_d] = events.StartMovingEastCommand()
        self.key_down_events[keyboard.K_w] = events.StartMovingNorthCommand()
        self.key_down_events[keyboard.K_a] = events.StartMovingWestCommand()
        self.key_down_events[keyboard.K_s] = events.StartMovingSouthCommand()
        self.key_up_events[keyboard.K_d] = events.StopMovingEastCommand()
        self.key_up_events[keyboard.K_w] = events.StopMovingNorthCommand()
        self.key_up_events[keyboard.K_a] = events.StopMovingWestCommand()
        self.key_up_events[keyboard.K_s] = events.StopMovingSouthCommand()

class PauseScreenKeyboardController(keyboard.KeyboardController):
    def setup(self):
        self.key_down_events[keyboard.K_ESCAPE] = events.QuitEvent()
        self.key_down_events[keyboard.K_SPACE] = events.TogglePausePhysicsCommand()
        self.key_down_events[keyboard.K_m] = events.ScreenShotCommand()
        self.key_down_events[keyboard.K_p] = events.TogglePausePhysicsCommand()

class GameOverScreenKeyboardController(keyboard.KeyboardController):
    def setup(self):
        self.key_down_events[keyboard.K_ESCAPE] = events.QuitEvent()
        self.key_down_events[keyboard.K_m] = events.ScreenShotCommand()
