#! /usr/bin/python
"""Geometry.
"""

from __future__ import division
import math

class Vector(object):
    """A two-dimensional vector of coordinates x and y, with maths.

    A Vector object has two coordinates: x and y.

    The class Vector provides a way of storing couple of coordinates such as
    sizes, positions, speeds, etc.  It also provide methods to manipulate them.
    Many methods are of mathematical nature and will add, subtract, etc..  Some
    methods are handy for performing deep copies.

    """
    def __init__(self, *args):
        """Initialize a Vector object with coordinates x and y.

        >>> v = Vector(1, 2)
        >>> print v.x
        1
        >>> print v.y
        2

        >>> print Vector()
        Vector(0, 0)
        >>> print Vector((1, 2))
        Vector(1, 2)
        >>> print Vector(Vector(1, 2))
        Vector(1, 2)

        """
        args_nb = len(args)
        if args_nb == 0:
            x = y = 0
        elif args_nb == 1:
            x, y = args[0] # Assume it's an iterable of length 2.
        elif args_nb == 2:
            x, y = args
        else:
            raise TypeError("Too many parameters.")
        self.x = x
        self.y = y
    
    @classmethod
    def fromDirection(cls, direction, norm=1):
        """Alternative constructor, specify direction and norm.

        Direction is in radians.
        The norm defaults at 1.

        """
        return cls(math.cos(direction) * norm,  math.sin(direction) * norm)

    def __repr__(self):
        """Return a string that Python can evaluate to create a similar object.

        >>> v = Vector(1, 2)
        >>> print repr(v)
        Vector(1, 2)

        """
        return "%s(%r, %r)" % (self.__class__.__name__, self.x, self.y)

    def __str__(self):
        return "%s(%g, %g)" % (self.__class__.__name__, self.x, self.y)

    def __len__(self):
        """Always return 2.

        >>> print len(Vector())
        2

        """
        return 2

    def __iter__(self):
        """Return an iterator over the coordinates x then y.

        >>> for coord in Vector(3, 4):
        ...     print coord
        3
        4

        """
        yield self.x
        yield self.y

    def __getitem__(self, where):
        """Return the coordinates.

        >>> v = Vector(3, 4)
        >>> print v[0]
        3
        >>> print v[1]
        4
        >>> print v[-1]
        4
        >>> print v[:2]
        (3, 4)
        >>> print v[::-1]
        (4, 3)

        """
        return (self.x, self.y)[where]

    def __setitem__(self, where, what):
        """Set the coordinates.

        >>> v = Vector(3, 4)
        >>> v[0] = 30
        >>> print v
        Vector(30, 4)
        >>> v[-1] = 40
        >>> print v
        Vector(30, 40)
        >>> v[::-1] = (100, 200)
        >>> print v
        Vector(200, 100)

        """
        tmp = [self.x, self.y]
        tmp[where] = what
        self.x, self.y = tmp

    def __eq__(self, other):
        """Return True if x and y are equal, False otherwise.

        >>> v1 = Vector(1, 2)
        >>> v2 = Vector(1, 2)
        >>> v3 = Vector(1, 9)
        >>> v4 = Vector(9, 2)
        >>> v5 = Vector(9, 9)
        >>> print v1 == v2
        True
        >>> print v1 == v3
        False
        >>> print v1 == v4
        False
        >>> print v1 == v5
        False

        """
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        """Return True if x or y differ, False otherwise.

        >>> v1 = Vector(1, 2)
        >>> v2 = Vector(1, 2)
        >>> v3 = Vector(1, 9)
        >>> v4 = Vector(9, 2)
        >>> v5 = Vector(9, 9)
        >>> print v1 != v2
        False
        >>> print v1 != v3
        True
        >>> print v1 != v4
        True
        >>> print v1 != v5
        True

        """
        return self.x != other.x or self.y != other.y

    def __add__(self, other):
        """Return a new Vector with added coordinates.

        Return a new object of the same class than the one on the left of the +
        sign.

        >>> v1 = Vector(1, 2)
        >>> v2 = Vector(3, 4)
        >>> v3 = v1 + v2
        >>> print v1
        Vector(1, 2)
        >>> print v2
        Vector(3, 4)
        >>> print v3
        Vector(4, 6)

        """
        return self.__class__(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        """Return a new Vector with subtracted coordinates.

        Return a new object of the same class than the one on the left of the -
        sign.

        >>> v1 = Vector(4, 6)
        >>> v2 = Vector(3, 4)
        >>> v3 = v1 - v2
        >>> print v1
        Vector(4, 6)
        >>> print v2
        Vector(3, 4)
        >>> print v3
        Vector(1, 2)

        """
        return self.__class__(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        """Return a new Vector with coordinates multiplied by a scalar.

        Return a new object of the same class than the one on the left of the *
        sign.

        >>> v1 = Vector(5, 6)
        >>> v2 = v1 * 2
        >>> print v1
        Vector(5, 6)
        >>> print v2
        Vector(10, 12)

        """
        return self.__class__(self.x * other, self.y * other)

    def __rmul__(self, other):
        """Return a new Vector with coordinates multiplied by a scalar.

        Return a new object of the same class than the one on the right of the
        * sign.

        >>> v1 = Vector(5, 6)
        >>> v2 = 2 * v1
        >>> print v1
        Vector(5, 6)
        >>> print v2
        Vector(10, 12)

        """
        return self.__class__(self.x * other, self.y * other)

#    def __div__(self, other):
#        """Return a new Vector with coordinates divided by a scalar.
#
#        Return a new object of the same class than the one on the left of the /
#        sign.
#
#        >>> v1 = Vector(5, 6)
#        >>> v2 = v1 / 2
#        >>> print v1
#        Vector(5, 6)
#        >>> print v2
#        Vector(2, 3)
#
#        """
#        return self.__class__(self.x / other, self.y / other)

    def __truediv__(self, other):
        """Return a new Vector with coordinates divided by a scalar.

        Return a new object of the same class than the one on the left of the /
        sign.

        >>> v1 = Vector(5, 6)
        >>> v2 = v1 / 2
        >>> print v1
        Vector(5, 6)
        >>> print v2
        Vector(2.5, 3)

        """
        return self.__class__(self.x / other, self.y / other)

    def __floordiv__(self, other):
        """Return a new Vector with coordinates divided by a scalar.

        Return a new object of the same class than the one on the left of the /
        sign.

        >>> v1 = Vector(5, 6)
        >>> v2 = v1 // 2
        >>> print v1
        Vector(5, 6)
        >>> print v2
        Vector(2, 3)

        """
        return self.__class__(self.x // other, self.y // other)

    def __and__(self, other):
        """Return a new Vector with the smallest coordinates.

        Think of 'and' to work like an intersection.  You end up with the
        smallest of both x and the smallest of both ys.

        Return a new object of the same class than the one on the left
        of the & sign.

        >>> v1 = Vector(1, 5)
        >>> v2 = Vector(3, 4)
        >>> v3 = v1 & v2
        >>> print v1
        Vector(1, 5)
        >>> print v2
        Vector(3, 4)
        >>> print v3
        Vector(1, 4)

        """
        return self.__class__(min([self.x, other.x]),
                              min([self.y, other.y]))

    def __or__(self, other):
        """Return a new Vector with the biggest coordinates.

        Think of 'or' to work like an union.  You end up with the
        greatest of both x and the smallest of both ys.

        Return a new object of the same class than the one on the left
        of the | sign.

        >>> v1 = Vector(1, 5)
        >>> v2 = Vector(3, 4)
        >>> v3 = v1 | v2
        >>> print v1
        Vector(1, 5)
        >>> print v2
        Vector(3, 4)
        >>> print v3
        Vector(3, 5)

        """
        return self.__class__(max([self.x, other.x]),
                              max([self.y, other.y]))

    def __iadd__(self, other):
        """Add the coordinates in place.

        >>> s = Vector(5, 6)
        >>> s += Vector(1, 2)
        >>> print s
        Vector(6, 8)

        """
        self.x += other.x
        self.y += other.y
        return self

    def __isub__(self, other):
        """Subtract the coordinates in place.

        >>> s = Vector(5, 7)
        >>> s -= Vector(1, 2)
        >>> print s
        Vector(4, 5)

        """
        self.x -= other.x
        self.y -= other.y
        return self

    def __imul__(self, other):
        """Multiply the coordinates in place.

        >>> s = Vector(5, 7)
        >>> s *= 2
        >>> print s
        Vector(10, 14)

        """
        self.x *= other
        self.y *= other
        return self

#    def __idiv__(self, other):
#        """Divide the coordinates in place.
#
#        >>> s = Vector(5, 6)
#        >>> s /= 2
#        >>> print s
#        Vector(2, 3)
#
#        """
#        self.x /= other
#        self.y /= other
#        return self

    def __ifloordiv__(self, other):
        """Divide the coordinates in place.

        >>> s = Vector(5, 6)
        >>> s //= 2
        >>> print s
        Vector(2, 3)

        """
        self.x //= other
        self.y //= other
        return self

    def __itruediv__(self, other):
        """Divide the coordinates in place.

        >>> s = Vector(5, 6)
        >>> s /= 2
        >>> print s
        Vector(2.5, 3)

        """
        self.x /= other
        self.y /= other
        return self

    def __iand__(self, other):
        """Assign the smallest coordinates in place.

        Think of 'and' to work like an intersection.  You end up with the
        smallest of both x and the smallest of both ys.

        >>> s = Vector(1, 5)
        >>> s &= Vector(3, 4)
        >>> print s
        Vector(1, 4)

        """
        self.x = min([self.x, other.x])
        self.y = min([self.y, other.y])
        return self

    def __ior__(self, other):
        """Assign the biggest coordinates in place.

        Think of 'or' to work like an union.  You end up with the
        greatest of both x and the smallest of both ys.

        >>> s = Vector(1, 5)
        >>> s |= Vector(3, 4)
        >>> print s
        Vector(3, 5)

        """
        self.x = max([self.x, other.x])
        self.y = max([self.y, other.y])
        return self

    def dot(self, other):
        """Return the dot product.

        >>> v1 = Vector(1, 2)
        >>> v2 = Vector(3, 4)
        >>> print v1.dot(v2)
        11
        >>> print 1 * 3 + 2 * 4
        11

        """
        return self.x * other.x + self.y * other.y

    def project(self, other):
        """Return the projection of the vector onto another."""
        return self.dot(other) * other.normalized()
    
    def iproject(self, other):
        """Replace the vector by its projection onto another."""
        self.x, self.y = self.dot(other) * other.normalized()
        return self

    def copy(self):
        """Create a new instance of Vector with the same x and y.

        >>> v1 = Vector(1, 2)
        >>> v2 = v1.copy()
        >>> print v1 == v2
        True
        >>> print v1 is v2
        False

        """
        return self.__class__(self.x, self.y)

    def icopy(self, other):
        """Copy the coordinates of other into itself, in place.

        >>> v1 = Vector(1, 2)
        >>> v2 = Vector(3, 4)
        >>> v1.icopy(v2)
        >>> print v1
        Vector(3, 4)
        >>> print v1 == v2
        True
        >>> print v1 is v2
        False

        """
        self.x = other.x
        self.y = other.y

    def norm(self):
        """Return the euclidian norm of the vector."""
        return (self.x ** 2 + self.y ** 2) ** .5

    def normsq(self):
        """Return the square of the euclidian norm of the vector.

        This method is provided as a way to optimize things a bit: for example,
        to find the longest vector, you don't need to compare the lengths, you
        can also compare the square of the lengths.  You save a bit of CPU time
        by not computing the square root.

        """        
        return self.x ** 2 + self.y ** 2

    def normalize(self):
        """Give the vector a norm of 1."""
        norm = (self.x ** 2 + self.y ** 2) ** .5
        self.x /= norm
        self.y /= norm

    def normalized(self):
        """Return a vector of norm 1 collinear to the current vector."""
        norm = (self.x ** 2 + self.y ** 2) ** .5
        return self.__class__(self.x / norm, self.y / norm)

    def normal(self):
        """Return a vector normal to the current vector.

        The returned vector has a norm of 1.

        Note that there are two possible normal vectors: two orientation for
        the same direction.  This algorithm return follows the trigonometric
        circle, operating a rotation of +pi/2.

                           ^
        ----->    gives    |
                           |

        """
        norm = (self.x ** 2 + self.y ** 2) ** .5
        return self.__class__(-self.y / norm, self.x / norm)

    def dist(self, other):
        """Return the distance to another vector.

        In that case, the two vectors are representing positions.

        """
        return ((other.x - self.x) ** 2 + (other.y - self.y) ** 2) ** .5

    def distsq(self, other):
        """Return the square of the distance to another vector.

        In that case, the two vectors are representing positions.
        
        This method is provided as a way to optimize things a bit: for example,
        to find the closest point, you don't need to compare distances, you
        can also compare the square of the distances.  You save a bit of CPU
        time by not computing the square root.

        """
        return (other.x - self.x) ** 2 + (other.y - self.y) ** 2
    def round(self, decimals):
        """Return a vector with x and y rounded at n decimals."""
        return self.__class__(round(self.x, decimals),
                              round(self.y, decimals))
    def iround(self, decimals):
        """Round x and y rounded at n decimals, internally."""
        self.x = round(self.x, decimals)
        self.y = round(self.y, decimals)

# pylint: disable-msg=C0103
# Invalid names.  Well, I'm doing geometry here, and I'll use the notations
# for points and vectors that I would use in real math.  Kinda.

def project(A, B, C):
    """Project C onto the line (AB).

    Return a 2-tuple : P, on_seg

     * P: the projection of C on (AB)
     * on_seg: boolean, whether or not P is on the segment [AB].

    Warning: if A == B you'll get a ZeroDivisionError.

    http://paulbourke.net/geometry/

    """
    AB = B - A
    AC = C - A
    # ratio = ac ab cos(BAC) / ab2
    ratio = AC.dot(AB) / AB.normsq()
    P = A + ratio * AB
    if not (0 <= ratio <= 1):
        print "    AB=", AB
        print "    AC=", AC
        print "    AC.AB=", AC.dot(AB)
        print "    ab2=", AB.normsq()
        print "    ratio=", ratio
    return P, 0 <= ratio <= 1


def InterLines(A, B, D, E):
    """Return intersection of lines (AB) and (DE).

    Return a 3-tuple (C, on_seg_AB, on_seg_DE)
    
     * C : coordinates of the intersection point.
     * on_seg_AB: true if intersection is part of the segment [AB].
     * on_seg_DE: true if intersection is part of the segment [DE].

    Raises ZeroDivisionError if the two lines are parallel.

    No check if the lines are coincident or if A = B.

    http://paulbourke.net/geometry/

    """
    x1, y1 = A
    x2, y2 = B
    x3, y3 = D
    x4, y4 = E

    x13 = x1 - x3
    y13 = y1 - y3

    x21 = x2 - x1
    y21 = y2 - y1

    x43 = x4 - x3
    y43 = y4 - y3
    denominator = y43 * x21 - x43 * y21
    ua = (x43 * y13 - y43 * x13) / denominator
    ub = (x21 * y13 - y21 * x13) / denominator
    x = x1 + ua * x21
    y = y1 + ua * y21
    return Vector(x, y), 0 <= ua <= 1, 0 <= ub <= 1


def DistPointToLine(A, B, C):
    """Compute the distance of point C to the line (AB).

    Return a 3-tuple : (d, I, on_seg)

     * d: the distance
     * I the intersection point
     * on_seg: boolean, whether or not I is on the segment. 

    Warning: if A == B you'll get a ZeroDivisionError.

    http://paulbourke.net/geometry/

    """
    x1, y1 = A
    x2, y2 = B
    x3, y3 = C

    x21 = x2 - x1
    y21 = y2 - y1
    u = ((x3 - x1) * x21 + (y3 - y1) * y21) / (x21 ** 2 + y21 ** 2)
    x = x1 + u * x21
    y = y1 + u * y21
    d = ((x3 - x) ** 2 + (y3 - y) ** 2) ** .5
    return d, Vector(x, y), 0 <= u <= 1


def Between(A, B, C):
    """Return whether or not B is between A and C.

    This is a very rough way of calculating it, they don't even need to be
    aligned.  But if they are, then this function is good.

    """
    ab = B.dist(A)
    ac = C.dist(A)
    bc = C.dist(B)
    return ab <= ac and bc <= ac
