#! /usr/bin/python
"""Event Management.

"""

import types
import weakref
import logging

LOGGER = logging.getLogger('evtman')

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
    to_log = True # Set to False in subclasses to avoid flooding the log.
    def __init__(self, *args):
        """Create a new event.

        The arguments must correspond to the `attribute` class variable.

        """
        object.__init__(self)
        if len(self.attributes) != len(args):
            msg = ("Incorrect number of arguments for %s: %i needed, "
                   "%i provided (attributes list: %r)." %
                   (self.__class__.__name__,
                    len(self.attributes), len(args), self.attributes))
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
        LOGGER.debug("Registering %r to %r..." % (listener, self))
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
        LOGGER.debug("%r registered to %r." % (listener, self))

    def unregister(self, listener):
        """Ask the EventManager to stop sending Events to that Listener."""
        LOGGER.debug("Unregistering %r from %r..." % (listener, self))
        did_something = False
        for handlers in self._handlers.values():
            if listener in handlers:
                del handlers[listener]
                did_something = True
        if not did_something:
            raise NotRegisteredError()
        LOGGER.debug("%r unregistered from %r..." % (listener, self))

    def post(self, event):
        """Add an Event to the event queue."""
        self._event_queue.append(event)
        if event.to_log:
            LOGGER.debug("POSTED: %r" % event)

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
                    # We are iterating over a copy of the items.  This
                    # guarantees us that we won't be hit by an error if the
                    # dictionary changes size ((un)registration) during the
                    # iteration.  However, this has some drawbacks:
                    # * If a listener gets unregistered during the iteration,
                    #   it will still receive the current event.
                    # * And if a listener gets registered, it won't receive it.
                    # I thought I could solve at least the first problem by
                    # using viewitems, but Weak*Dictionaries don't support that
                    # method.  The second problem is, I believe, less
                    # important.
                    handler(listener, event)
        del self._event_queue[:]

class SingleListener(Listener):
    """A Listener that listens to a single event manager.

    This class is created for convenience.  In most cases, Listeners will be
    interested in only one event_manager.  Therefore, SingleListener will be,
    most of the time, the class you want to create your Views Models and
    Controllers with.

    """
    def __init__(self, event_manager):
        """Registers the SingleListener to the given event manager."""
        Listener.__init__(self)
        self._event_manager = event_manager
        event_manager.register(self)
    def unregister(self):
        """Unregister the SingleListener from its event manager."""
        self._event_manager.unregister(self)
        self._event_manager = None
    def post(self, event):
        """Post an event through the SingleListener's event manager."""
        self._event_manager.post(event)
