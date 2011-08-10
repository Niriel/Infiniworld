#! /usr/bin/python
"""

"""
import evtman
import world

class PlayerController(evtman.SingleListener):
    def __init__(self, event_manager):
        evtman.SingleListener.__init__(self, event_manager)
        self._entity_id = None
    def onPlayerMovedEvent(self, event):
        if self._entity_id is not None:
            self.post(world.MoveEntityRequest(self._entity_id, event.vector))
    def onEntityCreatedEvent(self, event):
        # This is not serious of course.  We will need a better way of
        # assigning an entity to a player.
        self._entity_id = event.entity_id