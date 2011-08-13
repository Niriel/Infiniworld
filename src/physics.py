#! /usr/bin/python
"""Physics engine.

"""
# Standard library.
from __future__ import division
# My stuff.
from geometry import Vector

# pylint: disable-msg=C0103
# Invalid names.  Pylint thinks my variable names are too short.  I think not,
# I'm just sticking to mathematical notations.

def rk4(x, v, a, dt):
    """Returns final (position, velocity) tuple after time dt has passed.

    x: initial position (number-like object)
    v: initial velocity (number-like object)
    a: acceleration function a(x,v,dt) (must be callable)
    dt: timestep (number)

    Code taken from
    http://doswa.com/blog/2009/01/02/fourth-order-runge-kutta-numerical-integration/

    """
    # I removed some local variables in order to optimize in speed. The
    # variables I removed are x1, x2, x3 and x4.  They were used only once so
    # they did not need to exist.  They were used as first parameters for a1,
    # a2, a3 and a4.  I left them in the code as comments for clarity.

    # x1 = x
    v1 = v
    a1 = a(x, v1, 0)

    # x2 = x + 0.5 * v1 * dt
    v2 = v + 0.5 * a1 * dt
    a2 = a(x + 0.5 * v1 * dt, v2, dt / 2)

    # x3 = x + 0.5 * v2 * dt
    v3 = v + 0.5 * a2 * dt
    a3 = a(x + 0.5 * v2 * dt, v3, dt / 2)

    # x4 = x + v3 * dt
    v4 = v + a3 * dt
    a4 = a(x + v3 * dt, v4, dt)

    xf = x + dt * (v1 + 2 * v2 + 2 * v3 + v4) / 6
    vf = v + dt * (a1 + 2 * a2 + 2 * a3 + a4) / 6

    return xf, vf



class Particle(object):
    """A mathematical point with a mass, use it as center of gravity."""
    def __init__(self, mass, pos):
        """Initialize a new Particle object.
        
        mass: a float.
            0 is forbidden.
            float('inf') is accepted.
        
        pos: a Vector.
        
        Massless objects like moving at an infinite speed which breaks our
        simulation. Objects with an infinite mass can never change their speed.
        Handy for walls and other hard obstacles.
        
        """
        object.__init__(self)
        # Storing the 1 / mass forbids massless objects and allow infinite
        # masses.
        self.one_over_mass = 1 / mass
        self.pos = pos
        self.vel = Vector()
        self.forces = set()

    def __repr__(self):
        return "%s(id=0x%x, pos=%r, vel=%r)" % (self.__class__.__name__,
                                              id(self),
                                              self.pos, self.vel)

    def accel(self, pos, vel, dt):
        """Compute the acceleration from all the forces applied."""
        total_force = Vector()
        for force in self.forces:
            total_force += force(pos, vel, dt)
        return total_force * self.one_over_mass

    def integrate(self, dt):
        """Return the position and speed for the next dt.

        This is not directly applied to the particle since collisions are
        expected to happen along the way.

        """
        return rk4(self.pos, self.vel, self.accel, dt)

# pylint: disable-msg=R0903
# Too few public methods.  They're just dumb calculators, they don't need
# public methods.
class ConstantForce(object):
    """This force does not depend on time, position or speed.

    You can use that to model a character walking or running, or the wind,
    or gravity...

    """
    def __init__(self, vector):
        object.__init__(self)
        self.vector = vector
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.vector)
    def __call__(self, x, v, dt):
        return self.vector


class KineticFrictionForce(object):
    """Force proportional to speed.

    Used to slow down bodies.

    """
    def __init__(self, mu):
        """mu is a scalar: the coefficient of kinetic friction.

        To take energy from the particle, use a negative mu.

        """
        object.__init__(self)
        self.mu = mu
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.mu)
    def __call__(self, x, v, dt):
        return  v * self.mu

# pylint: enable-msg=R0903
