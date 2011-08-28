#! /usr/bin/python
"""Physics engine.

"""
# Standard library.
from __future__ import division
import math
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
        # masses.  1/mass is used during the integration of motion:
        # acceleration = forces / mass.
        self.one_over_mass = 1 / mass
        # mass is used in the elastic collision code.
        self.mass = mass
        # And the rest.
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

# In infiniworld, all the entities are circle.  Therefore we only have to check
# collisions between a circle and something else.

class Collision(object):
    """Represents a collision between a collider and a collidee.

    To sort the collisions by distance:
        from operator import attrgetter
        sorted(collisions, key=attrgetter('distance'))
    To find the closest:
        min(collisions, key=attrgetter('distance'))
    I haven't tested these yet though.

    """
    def __init__(self, distance, collider, collidee, penetration, entity=None):
        self.distance = distance
        # For the position correction:
        self.penetration = penetration
        # For the velocity correction (elastic collisions):
        self.collider = collider
        self.collidee = collidee
        # This is usef to signal the collidee that the collider bumped into it.
        # Leave to None if the collidee is not an entity.
        self.entity = entity
    def __str__(self):
        return "\n".join((self.__class__.__name__,
                          "    distance: %r" % self.distance,
                          "    penetration: %r" % self.penetration,
                          "    collider: %r" % self.collider,
                          "    collidee: %r" % self.collidee))
    def correctPosition(self):
        """Push the collider away from the collidee."""
        self.collider.pos += self.penetration
        # All these floating points calculations have errors and too often
        # we are stuck because the distance is 0.444444444444449 instead of .5,
        # and the correction does not work.  It may be smart to round the
        # positions.
    def correctVelocity(self):
        """Run the elastic collision code on the two bodies."""
        vder, vdee = elasticCollisionVelocities(self.collider, self.collidee,
                                                self.penetration.normalized())
        self.collider.vel = vder
        self.collidee.vel = vdee

class Body(Particle):
    """A body has a material and can be solid."""
    def __init__(self, mass, pos, solid, material):
        Particle.__init__(self, mass, pos)
        self.solid = solid
        self.material = material

class CircularBody(Body):
    """A physical body represented by a circle for collision purposes."""
    def __init__(self, mass, pos, solid, material, radius):
        Body.__init__(self, mass, pos, solid, material)
        self.radius = radius
    def collidesCircle(self, collider):
        """Is the circular `collider` colliding self?"""
        # If the distance between the centers is smaller than the sum of the
        # radii, there is collision.
        distance = self.pos.dist(collider.pos)
        radii = self.radius + collider.radius
        # Fight some annoying rounding errors.  I'm not just trying to hide a
        # real serious problem under the carpet here.  It's just that rounding
        # errors make `distance` smaller than `radii` on the 17th decimal. When
        # that tiny penetration vector is applied, the position does not change
        # and we keep colliding forever at every frame.  So it's not in the
        # correction part that I must hack this thing, that's in the detection
        # part.  Right here.  That feels dirty.
        #
        # if distance >= radii:
        if round(distance - radii, 6) >= 0:
            return None
        # Collision detected.  The penetration vector is collinear to the line
        # between the two centers.  It points from the center of the collidee
        # (self) to the center of the collider.
        try:
            penetration = ((collider.pos - self.pos).normalized() *
                           (radii - distance))
        except ZeroDivisionError:
            # The two bodies share the same center, let's give up.
            return None
        return Collision(distance, collider, self, penetration)


class RectangularBody(Body):
    """A physical body represented by a rectangle for collision purposes.

    The rectangle is axis-aligned.  That means that its edges are parallel to
    the x and y axis, they are horizontal and vertical.  You cannot tilt the
    rectangle.

    """
    def __init__(self, mass, pos, solid, material, size_x, size_y):
        Body.__init__(self, mass, pos, solid, material)
        self.size_x = size_x
        self.size_y = size_y
    def _withCorner(self, corner, collider):
        """`corner` is a vector."""
        distance = corner.dist(collider.pos)
        # I explain why I round in CircularBody.collidesCircle.
        if round(distance - collider.radius, 6) >= 0:
            return None
        try:
            penetration = ((collider.pos - corner).normalized() *
                           (collider.radius - distance))
        except ZeroDivisionError:
            # The two bodies share the same center, let's give up.
            return None
        return Collision(distance, collider, self, penetration)
    def _withHorizontalEdge(self, y_edge, sign, collider):
        """Sign = -1 if the other body is under the edge, and +1 if above.

        """
        # Here I look for the point on the collider's circle that's right
        # above or under its center.  If there is collision, that's because of
        # this point.
        y_other_body = collider.pos.y - sign * collider.radius
        # Here I am already measuring the penetration, actually.
        difference = y_edge - y_other_body
        # Except that if the sign of the penetration is not correct, there is
        # no collision.  I explain why I round in CircularBody.collidesCircle.
        if round(difference, 6) / sign <= 0:
            return None
        # Here there is collision, wrap it up.
        penetration = Vector(0, difference)
        return Collision(abs(difference), collider, self, penetration)
    def _withVerticalEdge(self, x_edge, sign, collider):
        """Sign = -1 if the other body is left ot the edge, and +1 if right.

        """
        # Here I look for the point on the collider's circle that's exactly
        # left or right of its center.  If there is collision, that's because
        # of this point.
        x_other_body = collider.pos.x - sign * collider.radius
        # Here I am already measuring the penetration, actually.
        difference = x_edge - x_other_body
        # Except that if the sign of the penetration is not correct, there is
        # no collision.  I explain why I round in CircularBody.collidesCircle.
        if round(difference, 6) / sign <= 0:
            return None
        # Here there is collision, wrap it up.
        penetration = Vector(difference, 0)
        return Collision(abs(difference), collider, self, penetration)
    def collidesCircle(self, collider):
        """Is the circular `collider` colliding self?"""
        x1 = self.pos.x - self.size_x / 2 # Left.
        x2 = x1 + self.size_x             # Right.
        y1 = self.pos.y - self.size_y / 2 # Bottom.
        y2 = y1 + self.size_y             # Top.
        x, y = collider.pos

        # Voronoi cells:
        #
        # 7 8 9
        # 4 5 6
        # 1 2 3
        #
        # 5 means you are inside the rectangle.
        # 1, 3, 7 and 9: the closest feature is a corner.
        # 2, 4, 6 and 8: the closest feature is an edge.

        if x <= x1 and y <= y1:
            return self._withCorner(Vector(x1, y1), collider) # Cell 1.
        elif x >= x2 and y <= y1:
            return self._withCorner(Vector(x2, y1), collider) # Cell 3.
        elif y <= y1:
            return self._withHorizontalEdge(y1, -1, collider) # Cell 2.

        elif x <= x1 and y >= y2:
            return self._withCorner(Vector(x1, y2), collider) # Cell 7.
        elif x >= x2 and y >= y2:
            return self._withCorner(Vector(x2, y2), collider) # Cell 9.
        elif y >= y2:
            return self._withHorizontalEdge(y2, 1, collider)  # Cell 8.

        elif x <= x1:
            return self._withVerticalEdge(x1, -1, collider)   # Cell 4.
        elif x >= x2:
            return self._withVerticalEdge(x2, 1, collider)    # Cell 6.
        # return None is implicit for cell 5.

#----------------------------  Elastic collision.  ----------------------------

def elasticCollisionSpeed(m1, v1, m2, v2):
    """Elastic collision, scalars."""
    if math.isinf(m1) and math.isinf(m2):
        # It's impossible to change the speed of an infinitely heavy thing. You
        # just don't do it.  Don't.
        return v1, v2
    if math.isinf(m1):
        # Typical of something bumping on a wall or something.  The wall desn't
        # feel a thing.
        return v1, -v2
    if math.isinf(m2):
        # Ditto.
        return -v1, v2
    # http://en.wikipedia.org/wiki/Elastic_collision
    u1 = (v1 * (m1 - m2) + 2 * m2 * v2) / (m1 + m2)
    u2 = (v2 * (m1 - m2) + 2 * m1 * v1) / (m1 + m2)
    return u1, u2

def elasticCollisionVelocities(part1, part2, normal):
    """Elastic collision, vectors."""
    # Decompose the velocity on the normal and tangential axis.
    v1n = part1.vel.dot(normal)    # These are scalar...
    v2n = part2.vel.dot(normal)
    v1t = part1.vel - v1n * normal # ... and these are vectors.
    v2t = part2.vel - v2n * normal
    # Elastic collision modifies the normal components only.
    u1n, u2n = elasticCollisionSpeed(part1.mass, v1n,
                                     part2.mass, v2n)
    # Apply material efficiencies.
    eff_n = part1.material.eff_n * part2.material.eff_n
    eff_t = part1.material.eff_t * part2.material.eff_t
    u1n *= eff_n
    u2n *= eff_n
    u1t = v1t * eff_t
    u2t = v2t * eff_t
    # Back to vectors.
    v1 = u1n * normal + u1t
    v2 = u2n * normal + u2t
    return v1, v2
