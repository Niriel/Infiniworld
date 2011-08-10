#! /usr/bin/python
"""

"""
import logging
import evtman
import log
import loop
import player
import pygame_
import ui
import world

def main():
    log.setup('infiniworld_solo.log')
    logger = logging.getLogger()
    logger.debug("Starting...")
    event_manager = evtman.EventManager()
    game_loop_controller = loop.GameLoopController(event_manager)
    ui_controller = ui.UiController(event_manager)
    world_ = world.WorldModel(event_manager)
    player_ = player.PlayerController(event_manager)
    with pygame_.Pygame():
        pygame_view = pygame_.PygameView(event_manager,
                                         u"Infiniworld", (800, 480))
        pygame_controller = pygame_.PygameController(event_manager)
        game_loop_controller.run()
    logger.debug("Stopping...")
    logging.shutdown()

if __name__ == '__main__':
    main()
