#! /usr/bin/python
"""Main program for playing Infiniworld in single-player mode.

"""
# Standard library.
import os
import logging
# My stuff.
import bunny
import directories
import infiniworld

def setUpLogging(file_name):
    path = os.path.join(directories.DIR_VAR_LOG, file_name)
    infiniworld.log.setup(path)

def main():
    """Run Infiniworld in single player mode."""
    setUpLogging('infiniworld_solo.log')
    logger = logging.getLogger()
    logger.info("Starting...")
    event_manager = infiniworld.evtman.EventManager()
    bunny.game.Game(event_manager)
    logger.info("Good bye!")
    logging.shutdown()

if __name__ == '__main__':
    PROFILE = False
    if PROFILE:
        try:
            import cProfile as profile
        except ImportError:
            # pylint: disable-msg=W0404
            # Complains about reimporting 'profile'.
            import profile
            # pylint: enable-msg=W0404
        profile.run('main()', 'profile.prf')
        import pstats
        pstats.Stats('profile.prf').sort_stats('time').print_stats(50)
    else:
        main()
