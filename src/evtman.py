#! /usr/bin/python
"""Event Management.

"""

import types
import weakref


class EvtManError(RuntimeError):
    """Base class for the exceptions of this module."""

class AlreadyRegisteredError(EvtManError):
    """Cannot register a Listener to the same EventManager twice.

    You should unregister it first.

    """

class NotRegisteredError(EvtManError):
    """Cannot unregister a Listener that is not registered in the first place.

    """

# pylint: disable-msg=R0903
# R0903: 25:Event: Too few public methods (0/2)
# I know, and I don't care, events don't need public methods, their constructor
# is all they need.
class Event(object):
    """Base abstract class for events used by Listeners to communicate."""
    attributes = ()
    def __init__(self, *args):
        """Create a new event.

        The arguments must correspond to the `attribute` class variable.

        """
        object.__init__(self)
        if len(self.attributes) != len(args):
            msg = ("Incorrect number of arguments: %i needed, %i provided "
                   "(attributes list: %r)." %
                   (len(self.attributes), len(args), self.attributes))
            raise TypeError(msg)
        pairs = zip(self.attributes, args)
        for name, value in pairs:
            setattr(self, name, value)
    def __repr__(self):
        pieces = []
        for attr_name in self.attributes:
            piece = "%s=%r" % (attr_name, getattr(self, attr_name))
            if len(piece) > 50:
                piece = piece[:50] + "..."
            pieces.append(piece)
        params = ', '.join(pieces)
        return "%s(%s)" % (self.__class__.__name__, params)
    def __str__(self):
        lines = [self.__class__.__name__]
        for attribute in self.attributes:
            lines.append("    %s = %r" % (attribute, getattr(self, attribute)))
        return '\n'.join(lines)
# pylint: enable-msg=R0903

class Listener(object):
    """Listeners react to Events when registered to an EventManager."""
    HANDLER_PREFIX = 'on'
    def isHandler(self, name):
        """Does `name` correspond to an Event handler?

        Event handlers must be methods of the current class and their name
        must start with the string 'on'.  For example: 'onCreatureMovedEvent'.

        It is expected that the string following 'on' correspond to a class
        name of an event.  From the previous example, the corresponding Event
        class is CreatureMovedEvent.  The handler 'onCreatureMovedEvent' reacts
        to the CreatureMovedEvent Events.

        Note: you can change the prefix for Event handlers from 'on' to
        whatever you like by changing the HANDLER_PREFIX class variable.

        By the way, `name` must correspond to an existing attribute of the
        object.  If not, AttributeError is raised.  I can't say whether or not
        something is a handler if that something doesn't even exist.

        """
        return (name.startswith(self.HANDLER_PREFIX) and
                type(getattr(self, name)) is types.MethodType)

    def getHandlers(self):
        """Returns a dictionary of Event class names:Event handlers pair.

        Listeners can listen to several types of Event.  They just need to have
        an Event handler for that type of Event.  The current FrameWork does
        it automatically by just looking at the method names of the Listener.

        For example, if a Listener has a method called 'onCreatureMovedEvent',
        this method automatically becomes the handler for the Events of class
        CreatureMovedEvent.

        The current function scans all the attributes of the current Listener
        instances looking for handlers.  It returns a dictionary.  The keys
        are strings corresponding to the name of the Event classes the Listener
        wants to listen to, and the values are the corresponding handlers for
        these Events.

        """
        result = {}
        event_name_start = len(self.HANDLER_PREFIX)
        for name in dir(self):
            if self.isHandler(name):
                event_name = name[event_name_start:]
                result[event_name] = getattr(self, name)
        return result

class EventManager(object):
    """An EventManager forward Events to the registered Listeners."""
    def __init__(self):
        object.__init__(self)
        # Dictionary of handlers interested by events. The key is an event
        # class name and the values are a set of handlers. This allows us to
        # quickly find all the handlers interested in an event, no matter which
        # Listener they belong to.  We use weak references for the storing the
        # handlers. The values of that dictionary are WeakKeyDictionary
        # objects; the keys are Listeners and the values are their handler for
        # the Event. When a Listener is garbage collected, it disappears from
        # the dictionary.  This is done for two reasons:
        #
        # 1: The event manager is not the owner of these Listeners.  They
        #    should be owned by other Listeners (The WorldModel contains all
        #    the CreatureModel objects for instance), or by something else like
        #    the main function which instantiates the top-level models views
        #    and controllers.  This is a bit philosophical.
        # 2: Doing it that way can break sometimes.  If a Listener gets
        #    garbage-collected while we are iterating on a WeakDictionary, we
        #    expect weird things to happen, including "RuntimeError: dictionary
        #    changed size during iteration".  This is good, because we can see
        #    we forgot to properly unregister.
        self._handlers = {}
        # Events posted with the post method of this class are appended to the
        # end of this queue.  Events are processed in the order they are
        # posted.
        self._event_queue = []

    def strHandlers(self):
        """Return a string of events and handlers on each line.  For debugging.

        """
        result = ["handlers:"]
        for event_name, handlers in self._handlers.iteritems():
            result.append("    %s : %s" % (event_name, handlers.values()))
        return '\n'.join(result)

    def register(self, listener):
        """Tell the EventManager to send Events to that Listener's handlers."""
        handlers_for_listener = listener.getHandlers()
        # Each handler is stored in a set of handlers corresponding to their
        # Event class name.
        for event_name, handler in handlers_for_listener.iteritems():
            if event_name in self._handlers:
                handlers = self._handlers[event_name]
            else:
                handlers = weakref.WeakKeyDictionary()
                self._handlers[event_name] = handlers
            if listener in handlers:
                raise AlreadyRegisteredError()
            else:
                # Here I only store the function of the bound method object.
                # If I don't, I keep a pointer to the instance, and therefore
                # it never leaves the dictionary.
                handlers[listener] = handler.im_func

    def unregister(self, listener):
        """Ask the EventManager to stop sending Events to that Listener."""
        did_something = False
        for handlers in self._handlers.values():
            if listener in handlers:
                del handlers[listener]
                did_something = True
        if not did_something:
            raise NotRegisteredError()

    def post(self, event):
        """Add an Event to the event queue."""
        self._event_queue.append(event)

    def pump(self):
        """Sends all the events of the event queue to the appropriate handlers.

        """
        for event in self._event_queue:
            # It is safe to iterate over that list even if new events are
            # appended during the iteration.
            event_name = event.__class__.__name__
            handlers = self._handlers.get(event_name, None)
            if handlers:
                for listener, handler in handlers.items():
                    # I iterate over a copy of the items because the copy is
                    # guaranteed not to change in size, while it is very
                    # possible to have the handlers dictionary change during
                    # the iteration because listeners can be (un)registered.
                    handler(listener, event)
        del self._event_queue[:]

def example():
    class CharacterMovedEvent(Event):
        attributes = ('character_id', 'position_from', 'position_to')
    class CharacterView(Listener):
        def __init__(self, character_id):
            Listener.__init__(self)
            self._character_id = character_id
            self._x = self._y = 0
        def __str__(self):
            return "%s: pos = (%i, %i)" % (self._character_id,
                                           self._x, self._y)
        def onCharacterMovedEvent(self, event):
            if event.character_id == self._character_id:
                self._x = event.position_to[0] * 32
                self._y = 480 - event.position_to[1] * 32
    #
    bunny_view = CharacterView('bunny')
    hamster_view = CharacterView('hamster')
    event_manager = EventManager()
    event_manager.register(bunny_view)
    event_manager.register(hamster_view)
    #
    event = CharacterMovedEvent('bunny', (0, 0), (1, 2))
    event_manager.post(event)
    event_manager.pump()
    #
    print bunny_view
    print hamster_view

    class CharacterModel(Listener):
        def __init__(self, event_manager, character_id):
            Listener.__init__(self)
            self._event_manager = event_manager
            self._character_id = character_id
            self._x = self._y = 0
        def moveTo(self, new_x, new_y):
            old_x = self._x
            old_y = self._y
            self._x = new_x
            self._y = new_y
            event = CharacterMovedEvent(self._character_id, (old_x, old_y), (new_x, new_y))
            self._event_manager.post(event)

    hamster_model = CharacterModel(event_manager, 'hamster')
    event_manager.register(hamster_model)
    hamster_model.moveTo(3, 3)
    event_manager.pump()
    print hamster_view

if __name__ == '__main__':
    example()
