#! /usr/bin/python
"""Event Management test suite.

"""

import unittest
import evtman
from evtman import Event, Listener, EventManager

# pylint: disable-msg=R0904
# Because unit tests have tons of public methods and that's normal.

# pylint: disable-msg=W0212
# Because I know what I'm doing when I use a protected attribute in a test.

#----------  Helper classes.  ----------
egg_plus_spam = 0

class SubEvent(Event):
    attributes = ('egg', 'spam')

class SubListener(Listener):
    def onSubEvent(self, event):
        global egg_plus_spam
        egg_plus_spam += event.egg + event.spam

#----------  Test suite.  ----------
class TestEvent(unittest.TestCase):
    """Test the evtman.Event class."""

    def testInit(self):
        """Event.__init__ doesn't crash."""
        unused = Event()

    def testInitWrongParams(self):
        """Event.__init__ complains when too many parameters."""
        # Here we create an Event with one parameter: 666.  Event does not
        # expect any, so it should raise a TypeError.
        self.assertRaises(TypeError, Event, 666)

    def testSubClassInit(self):
        """Event.__init__ doesn't crash on subclass."""
        event = SubEvent(666, 42)
        # pylint: disable-msg=E1101
        # Yes they have an egg and spam member, but Pylint doesn't know it.
        self.assertEqual(event.egg, 666)
        self.assertEqual(event.spam, 42)

    def testSubClassWrongParams(self):
        """Event.__init__ complains when wrong nb of parameters on subclass."""
        # Not enough parameters:
        self.assertRaises(TypeError, SubEvent, 666)
        # Too many:
        self.assertRaises(TypeError, SubEvent, 666, 42, "bunny")


class TestListener(unittest.TestCase):
    """Test the evtman.Listener class."""
    def testInit(self):
        """Listener.__init__ doesn't crash."""
        unused = Listener()
    def testIsHandler(self):
        """Listener.isHandler identifies handlers."""
        listener = SubListener()
        self.assertTrue(listener.isHandler('onSubEvent'))
        self.assertFalse(listener.isHandler('__str__'))
    def testGetHandlers(self):
        """Listener.isHandler return handlers."""
        listener = Listener()
        handlers = listener.getHandlers()
        self.assertEquals(len(handlers), 0)
        #
        listener = SubListener()
        handlers = listener.getHandlers()
        self.assertEquals(len(handlers), 1)
        self.assertEquals(handlers['SubEvent'], listener.onSubEvent)

class TestEventManager(unittest.TestCase):
    def testInit(self):
        """EventManager.__init__ doesn't crash."""
        unused = EventManager()

    def testRegister(self):
        """EventManager.register adds the listener to its list."""
        event_manager = EventManager()
        listener = SubListener()
        event_manager.register(listener)
        handlers = event_manager._handlers
        self.assertEquals(len(handlers), 1)
        self.assertEquals(len(handlers['SubEvent']), 1)
        self.assertEquals(handlers['SubEvent'][listener], listener.onSubEvent.im_func)

    def testRegisterTwice(self):
        """EventManager.register breaks if already registered."""
        event_manager = EventManager()
        listener = SubListener()
        event_manager.register(listener)
        self.assertRaises(evtman.AlreadyRegisteredError,
                          event_manager.register, listener)

    def testUnregister(self):
        """EventManager.unregister removes the handlers of a listener."""
        event_manager = EventManager()
        listener1 = SubListener()
        listener2 = SubListener()
        event_manager.register(listener1)
        event_manager.register(listener2)
        event_manager.unregister(listener1)
        self.assertFalse(listener1 in event_manager._handlers['SubEvent'])
        self.assertTrue(listener2 in event_manager._handlers['SubEvent'])

    def testUnregisterIfNotRegistered(self):
        """EventManager.unregister complains if not registered."""
        event_manager = EventManager()
        listener = SubListener()
        self.assertRaises(evtman.NotRegisteredError,
                          event_manager.unregister, listener)
        event_manager.register(listener)
        event_manager.unregister(listener)
        self.assertRaises(evtman.NotRegisteredError,
                          event_manager.unregister, listener)

    def testWeakReference(self):
        """EventManager forgets dead listeners."""
        event_manager = EventManager()
        listener = SubListener()
        event_manager.register(listener)

        del listener
        import gc
        gc.collect()

        handlers = event_manager._handlers
        self.assertEquals(len(handlers), 1)
        self.assertEquals(len(handlers['SubEvent']), 0)

    def testPostAndPump(self):
        """EventManager.pump sends all the posted events to all the listeners.

        """
        event_manager = EventManager()
        listener1 = SubListener()
        listener2 = SubListener()
        event_manager.register(listener1)
        event_manager.register(listener2)
        event_manager.register(Listener()) # This one won't react.
        event1 = SubEvent(666, 42)
        event2 = SubEvent(13, 7)
        global egg_plus_spam
        egg_plus_spam = 0
        event_manager.post(event1)
        event_manager.post(event2)
        event_manager.post(Event()) # This one won't trigger anything.
        event_manager.pump()
        self.assertEquals(egg_plus_spam, (666 + 42 + 13 + 7) * 2)

if __name__ == "__main__":
    unittest.main()
