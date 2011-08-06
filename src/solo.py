#! /usr/bin/python
"""

"""
import pygame

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

if __name__ == '__main__':
    print "Initializing..."
    with Pygame():
        display = pygame.display.set_mode((800, 480))
        print "Insert game here."
    print "Bye!"
