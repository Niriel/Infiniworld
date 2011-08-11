#! /usr/bin/python
"""Main program for playing Infiniworld in single-player mode.

"""
# Standard library.
import logging
# My stuff.
import evtman
import log
import loop
import player
import pygame_
import world

def main():
    """Run Infiniworld in single player mode."""
    log.setup('infiniworld_solo.log')
    logger = logging.getLogger()
    logger.debug("Starting...")
    event_manager = evtman.EventManager()
    game_loop_controller = loop.GameLoopController(event_manager)
    world_model = world.WorldModel(event_manager)
    player_controller = player.PlayerController(event_manager)
    with pygame_.Pygame():
        pygame_view = pygame_.PygameView(event_manager,
                                         u"Infiniworld", (800, 480))
        pygame_controller = pygame_.PygameController(event_manager)
        # Run the game until a QuitEvent is posted.
        game_loop_controller.run()
        logger.info("Stopping...")
    # Unregistering at the end is not necessary but I do it so that PyDev and
    # PyLint stop complaining about unused variables.
    game_loop_controller.unregister()
    world_model.unregister()
    player_controller.unregister()
    pygame_view.unregister()
    pygame_controller.unregister()
    #
    logging.shutdown()

if __name__ == '__main__':
    main()
