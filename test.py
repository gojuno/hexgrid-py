import unittest
import logging

from hexgrid import (
    Point, Hex, Grid, OrientationFlat, OrientationPointy,
    point_in_geometry
)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


class TestHexgrid(unittest.TestCase):

    def assertHexEqual(self, e, r):
        if(e.q != r.q or e.r != r.r):
            self.fail("{} != {}".format(e, r))

    def assertPointEqual(self, e, r, precision):
        if(abs(e.x-r.x) > precision or abs(e.y - r.y) > precision):
            self.fail("{} != {}".format(e, r))

    def test_flat(self):
        grid = Grid(OrientationFlat, Point(10, 20), Point(20, 10))

        self.assertHexEqual(Hex(0, 37), grid.hex_at(Point(13, 666)))
        self.assertHexEqual(Hex(22, -11), grid.hex_at(Point(666, 13)))
        self.assertHexEqual(Hex(-1, -39), grid.hex_at(Point(-13, -666)))
        self.assertHexEqual(Hex(-22, 9), grid.hex_at(Point(-666, -13)))

    def test_coordinates_flat(self):
        grid = Grid(OrientationFlat, Point(10, 20), Point(20, 10))
        hex = grid.hex_at(Point(666, 666))

        self.assertPointEqual(
            Point(670.00000, 660.85880), grid.hex_center(hex), 0.00001)

        corners = grid.hex_corners(hex)

        expected_corners = [
            Point(690.00000, 660.85880),
            Point(680.00000, 669.51905),
            Point(660.00000, 669.51905),
            Point(650.00000, 660.85880),
            Point(660.00000, 652.19854),
            Point(680.00000, 652.19854),
        ]
        for expected_point, point in zip(expected_corners, corners):
            self.assertPointEqual(expected_point, point, 0.00001)

    def test_pointy(self):
        grid = Grid(OrientationPointy, Point(10, 20), Point(20, 10))

        self.assertHexEqual(Hex(-21, 43), grid.hex_at(Point(13, 666)))
        self.assertHexEqual(Hex(19, 0), grid.hex_at(Point(666, 13)))
        self.assertHexEqual(Hex(22, -46), grid.hex_at(Point(-13, -666)))
        self.assertHexEqual(Hex(-19, -2), grid.hex_at(Point(-666, -13)))

    def test_coordinates_pointy(self):
        grid = Grid(OrientationPointy, Point(10, 20), Point(20, 10))
        hex = grid.hex_at(Point(666, 666))

        self.assertPointEqual(
            Point(650.85880, 665.00000), grid.hex_center(hex), 0.00001)

        corners = grid.hex_corners(hex)

        expected_corners = [
            Point(668.17930, 670.00000),
            Point(650.85880, 675.00000),
            Point(633.53829, 670.00000),
            Point(633.53829, 660.00000),
            Point(650.85880, 655.00000),
            Point(668.17930, 660.00000),
        ]
        for expected_point, point in zip(expected_corners, corners):
            self.assertPointEqual(expected_point, point, 0.00001)

    def test_neighbors(self):
        grid = Grid(OrientationFlat, Point(10, 20), Point(20, 10))
        hex = grid.hex_at(Point(666, 666))
        expected_codes = [
            920, 922, 944, 915, 921, 923, 945, 916, 918,
            926, 948, 917, 919, 925, 927, 960, 962, 968]

        neighbors = grid.hex_neighbors(hex, 2)

        for expected_code, neighbor_hex in zip(expected_codes, neighbors):
            code = grid.hex_to_code(neighbor_hex)
            self.assertEqual(code, expected_code, neighbor_hex)

    def test_point_in_geometry(self):
        square_geometry = [
            Point(0, 0), Point(10, 0),
            Point(10, 0), Point(10, 10),
            Point(10, 10), Point(0, 10),
            Point(0, 10), Point(0, 0),
        ]
        test_points = [
            Point(5, 5), Point(5, 8),
            Point(-10, 5), Point(0, 5),
            Point(10, 5), Point(8, 5),
            Point(10, 10)
        ]
        expected_results = [
            True, True,
            False, False,
            False, True,
            False
        ]
        for r, p in zip(expected_results, test_points):
            self.assertTrue(
                r == point_in_geometry(p, square_geometry), p)

        square_hole = [
            Point(0, 0), Point(10, 0),
            Point(10, 0), Point(10, 10),
            Point(10, 10), Point(0, 10),
            Point(0, 10), Point(0, 0),
            Point(2.5, 2.5), Point(7.5, 2.5),
            Point(7.5, 2.5), Point(7.5, 7.5),
            Point(7.5, 7.5), Point(2.5, 7.5),
            Point(2.5, 7.5), Point(2.5, 2.5)
        ]
        expected_results = [
            False, True,
            False, False,
            False, True,
            False
        ]
        for r, p in zip(expected_results, test_points):
            self.assertTrue(
                r == point_in_geometry(p, square_hole), p)

        strange = [
            Point(0, 0), Point(2.5, 2.5),
            Point(2.5, 2.5), Point(0, 10),
            Point(0, 10), Point(2.5, 7.5),
            Point(2.5, 7.5), Point(7.5, 7.5),
            Point(7.5, 7.5), Point(10, 10),
            Point(10, 10), Point(10, 0),
            Point(10, 0), Point(2.5, 2.5)
        ]
        expected_results = [
            True, False,
            False, False,
            False, True,
            False
        ]
        for r, p in zip(expected_results, test_points):
            self.assertTrue(
                r == point_in_geometry(p, strange), (p, point_in_geometry) )

        exagon = [
            Point(3, 0), Point(7, 0),
            Point(7, 0), Point(10, 5),
            Point(10, 5), Point(7, 10),
            Point(7, 10), Point(3, 10),
            Point(3, 10), Point(0, 5),
            Point(0, 5), Point(3, 0)
        ]
        expected_results = [
            True, True,
            False, False,
            False, True,
            False
        ]
        for r, p in zip(expected_results, test_points):
            self.assertTrue(
                r == point_in_geometry(p, exagon), p)

    def test_region(self):
        grid = Grid(OrientationFlat, Point(10, 20), Point(20, 10))
        geometry = [
            Point(20, 19.99999), Point(20, 40), Point(40, 60),
            Point(60, 40), Point(50, 30), Point(40, 40)
        ]
        region = grid.make_region(geometry)
        hexes = region.hexes
        expected_codes = [0, 2, 1, 3, 9, 4]

        self.assertEqual(len(hexes), len(expected_codes))
        for hex, expected_code in zip(hexes, expected_codes):
            code = grid.hex_to_code(hex)
            self.assertEqual(code, expected_code)
