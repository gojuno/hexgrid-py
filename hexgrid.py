from collections import namedtuple
import math
import sys
from morton import Morton

try:
    from shapely import geometry as shapely_geometry
except ImportError:
    shapely_geometry = None

Point = namedtuple('Point', ['x', 'y'])


def is_point_on_line(point, start, end):
    if start.x <= point.x and point.x <= end.x:
        se = Point((end.x - start.x), (end.y - start.y))
        sp = Point((point.x - start.x), (point.y - start.y))
        return (sp.x*se.y - sp.y*se.x) == 0
    return False


def ray_intersects_segment(point, start, end):
    # type: (Point, Point, Point) -> bool
    '''
        Check if the point is inside or outside the polygon
        using the ray-casting algorithm
        (see http://rosettacode.org/wiki/Ray-casting_algorithm)

        point : the point from which the ray starts
        start : the end-point of the segment with the smallest y coordinate
                ('start' must be "below" 'end')
        end : the end-point of the segment with the greatest y coordinate
              ('end' must be "above" 'start')
    '''

    if start.y > end.y:
        start, end = end, start

    if point.y == start.y or point.y == end.y:
        point = Point(point.x, point.y + 0.00001)

    if point.y > end.y or point.y < start.y or point.x > max(start.x, end.x):
        return False

    if point.x < min(start.x, end.x):
        return True

    m_blue = (point.y - start.y) / float(point.x - start.x) \
        if point.x != start.x else sys.float_info.max

    m_red = (end.y - start.y) / float(end.x - start.x) \
        if start.x != end.x else sys.float_info.max

    return m_blue >= m_red


def point_in_geometry(point, geometry):
    # type: (Point, list) -> bool

    # point does not belong to polygon if located on some edge
    for i in range(1, len(geometry)):
        if is_point_on_line(point, geometry[i-1], geometry[i]):
            return False
    if is_point_on_line(point, geometry[0], geometry[-1]):
        return False

    contains = ray_intersects_segment(point, geometry[-1], geometry[0])
    for i in range(1, len(geometry)):
        if ray_intersects_segment(point, geometry[i - 1], geometry[i]):
            contains = not contains

    return contains

class Hex(namedtuple('Hex', ['q', 'r'])):

    @property
    def s(self):
        return -(self.q + self.r)


class FractionalHex(Hex):

    def to_hex(self):
        q = round(self.q)
        r = round(self.r)
        s = round(self.s)
        dq = abs(q - self.q)
        dr = abs(r - self.r)
        ds = abs(s - self.s)
        if(dq > dr and dq > ds):
            q = -(r + s)
        elif(dr > ds):
            r = -(q + s)
        return Hex(int(q), int(r))


_Orientation = namedtuple(
    'Orientation',
    ['f', 'b', 'startAngle', 'sinuses', 'cosinuses'])


class Orientation(_Orientation):
    def __new__(cls, f, b, start_angle):
        assert type(f) is list and len(f) == 4
        assert type(b) is list and len(b) == 4
        # prehash angles
        sinuses = []
        cosinuses = []
        for i in range(6):
            angle = 2.0 * math.pi * (i + start_angle)/6.0
            sinuses.append(math.sin(angle))
            cosinuses.append(math.cos(angle))
        return super(Orientation, cls).__new__(cls, f, b, start_angle, sinuses, cosinuses)


OrientationPointy = Orientation(
    f=[math.sqrt(3.0), math.sqrt(3.0)/2.0, 0.0, 3.0/2.0],
    b=[math.sqrt(3.0)/3.0, -1.0/3.0, 0.0, 2.0/3.0],
    start_angle=0.5)


OrientationFlat = Orientation(
    f=[3.0/2.0, 0.0, math.sqrt(3.0)/2.0, math.sqrt(3.0)],
    b=[2.0/3.0, 0.0, -1.0/3.0, math.sqrt(3.0)/3.0],
    start_angle=0.0)


_Grid = namedtuple('Grid', ['orientation', 'origin', 'size', 'morton'])


class Grid(_Grid):

    def __new__(cls, orientation, origin, size, morton=None):
        # type: (Orientation, Point, Point, Morton) -> Grid
        morton = morton or Morton()
        return super(Grid, cls).__new__(cls, orientation, origin, size, morton)

    def hex_to_code(self, hex):
        # type: (Hex) -> int
        return self.morton.pack(hex.q, hex.r)

    def hex_from_code(self, code):
        # type: (int) -> Hex
        return Hex(*self.morton.unpack(code))

    def hex_at(self, point):
        # type: (Point) -> Hex
        x = (point.x - self.origin.x) / float(self.size.x)
        y = (point.y - self.origin.y) / float(self.size.y)
        q = self.orientation.b[0]*x + self.orientation.b[1] * y
        r = self.orientation.b[2]*x + self.orientation.b[3] * y
        return FractionalHex(q, r).to_hex()

    def hex_center(self, hex):
        # type: (Hex) -> Point
        f = self.orientation.f
        x = (f[0] * hex.q + f[1]*hex.r)*self.size.x + self.origin.x
        y = (f[2] * hex.q + f[3]*hex.r)*self.size.y + self.origin.y
        return Point(x, y)

    def hex_corners(self, hex):
        # type: (Hex) -> list
        corners = []
        center = self.hex_center(hex)
        for i in range(6):
            x = self.size.x*self.orientation.cosinuses[i] + center.x
            y = self.size.y*self.orientation.sinuses[i] + center.y
            corners.append(Point(x, y))
        return corners

    def hex_neighbors(self, hex, layers):
        # type: (Hex, int) -> list
        neighbors = []
        for q in range(-layers, layers+1):
            r1 = max(-layers, -q-layers)
            r2 = min(layers, -q+layers)
            for r in range(r1, r2+1):
                if q == 0 and r == 0:
                    continue

                neighbors.append(Hex(q+hex.q, r+hex.r))
        return neighbors

    def _make_region(self, geometry):
        # type: (list) -> Region
        x, y = zip(*geometry)
        hexes = [
            self.hex_at(Point(min(x), min(y))),
            self.hex_at(Point(min(x), max(y))),
            self.hex_at(Point(max(x), max(y))),
            self.hex_at(Point(max(x), min(y))),
        ]
        q, r = zip(*hexes)
        q_min = min(q) - 1
        q_max = max(q) + 1
        r_min = min(r) - 1
        r_max = max(r) + 1

        def any_point_in_geometry(ps, g):
            for p in ps:
                if point_in_geometry(p, g):
                    return True

        hexes = []
        lookup = {}
        for q in range(q_min, q_max+1):
            for r in range(r_min, r_max+1):
                hex = Hex(q, r)
                corners = self.hex_corners(hex)
                if(
                        any_point_in_geometry(corners, geometry) or
                        any_point_in_geometry(geometry, corners)
                ):
                    hexes.append(hex)
                    lookup[self.hex_to_code(hex)] = True

        return Region(self, hexes, lookup)

    def _shapely_make_region(self, geometry):
        # type: (list) -> Region
        polygon = shapely_geometry.Polygon(geometry)
        (minx, miny, maxx, maxy) = polygon.bounds

        x, y = zip(*geometry)
        hexes = [
            self.hex_at(Point(minx, miny)),
            self.hex_at(Point(minx, maxy)),
            self.hex_at(Point(maxx, maxy)),
            self.hex_at(Point(maxx, miny)),
        ]
        q, r = zip(*hexes)
        q_min = min(q) - 1
        q_max = max(q) + 1
        r_min = min(r) - 1
        r_max = max(r) + 1

        hexes = []
        lookup = {}
        for q in range(q_min, q_max+1):
            for r in range(r_min, r_max+1):
                hex = Hex(q, r)
                corners = self.hex_corners(hex)
                if polygon.intersects(shapely_geometry.Polygon(corners)):
                    hexes.append(hex)
                    lookup[self.hex_to_code(hex)] = True

        return Region(self, hexes, lookup)

    if shapely_geometry:
        make_region = _shapely_make_region
    else:
        make_region = _make_region


class Region(namedtuple('Region', ['grid', 'hexes', 'lookup'])):

    def union(self, region):
        # type: (Region) -> Region
        if self.grid is not region.grid:
            raise ValueError("grid is different")

        hexes = list(self.hexes)
        lookup = dict(self.lookup)
        for hex in region.hexes:
            if self.contains(hex):
                continue
            hexes.append(hex)
            lookup[self.grid.hex_to_code(hex)] = True

    def contains(self, hex):
        # type: (Hex) -> bool
        return self.grid.hex_to_code(hex) in self.lookup
