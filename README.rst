HexGrid
=======

Basics
------

Configurable hex grid on abstract surface.

Example
-------

.. code-block:: python

    import hexgrid
    import morton

    center = hexgrid.Point(0, 0)
    size = hexgrid.Point(20, 10)
    grid = hexgrid.Grid(hexgrid.OrientationFlat, center, size, morton.Morton(2, 32))
    hex = grid.hex_at(hexgrid.Point(50, 50))
    code = grid.hex_to_code(hex)
    restored_hex = grid.hex_from_code(code)
    neighbors = grid.hex_neighbors(hex, 2)
    points := [
        hexgrid.Point(0, 0), hexgrid.Point(0, 10),
        hexgrid.Point(10, 10), hexgrid.Point(10, 0)
    ]
    region = grid.make_region(points)
    hexes_in_region = region.hexes
