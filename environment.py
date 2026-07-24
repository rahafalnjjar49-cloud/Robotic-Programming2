"""
environment.py
--------------
Defines the warehouse grid (Environment / Warehouse), the types of cells that can
exist on it, and helper station classes (ChargingStation, DeliveryStation, Shelf).

The map can be loaded from a JSON file so the warehouse layout is fully
configurable without touching code.
"""

import json
from enum import Enum


class CellType(Enum):
    EMPTY = "."
    WALL = "#"
    SHELF = "S"
    CHARGER = "C"
    LOADING = "L"
    DELIVERY = "D"


class Warehouse:
    """
    Represents the 2D warehouse grid.

    grid[y][x] -> CellType
    Robots, packages, etc. are NOT stored on the grid itself; the grid only
    describes static terrain. Dynamic occupancy (robots) is tracked separately
    by the Simulation/CollisionManager so that multiple systems can query it
    independently (this keeps the design modular, per the OOP requirement).
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[CellType.EMPTY for _ in range(width)] for _ in range(height)]

        # Convenience lists of important coordinates, filled in while loading
        self.charging_stations = []
        self.loading_stations = []
        self.delivery_stations = []

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #
    @classmethod
    def from_json(cls, path):
        """Load a warehouse layout from a JSON file.

        Expected JSON format:
        {
            "width": 12,
            "height": 8,
            "layout": [
                "############",
                "#..S...C...#",
                ...
            ]
        }
        Each character in `layout` maps to a CellType via its `.value`.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        width = data["width"]
        height = data["height"]
        wh = cls(width, height)

        char_to_type = {ct.value: ct for ct in CellType}

        for y, row in enumerate(data["layout"]):
            for x, ch in enumerate(row):
                cell_type = char_to_type.get(ch, CellType.EMPTY)
                wh.grid[y][x] = cell_type
                if cell_type == CellType.CHARGER:
                    wh.charging_stations.append((x, y))
                elif cell_type == CellType.LOADING:
                    wh.loading_stations.append((x, y))
                elif cell_type == CellType.DELIVERY:
                    wh.delivery_stations.append((x, y))

        return wh

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        """A cell is walkable if it is inside the grid and not a wall/shelf."""
        if not self.in_bounds(x, y):
            return False
        return self.grid[y][x] not in (CellType.WALL, CellType.SHELF)

    def neighbors(self, x, y):
        """4-connected neighbors that are walkable (used by the path planner)."""
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return [(nx, ny) for nx, ny in candidates if self.is_walkable(nx, ny)]

    def nearest_station(self, stations, x, y):
        """Return the closest station (Manhattan distance) from a list of coords."""
        if not stations:
            return None
        return min(stations, key=lambda s: abs(s[0] - x) + abs(s[1] - y))

    # ------------------------------------------------------------------ #
    # Rendering (text mode)
    # ------------------------------------------------------------------ #
    def render(self, robots, packages=None):
        """Print an ASCII view of the warehouse with robots overlaid."""
        robot_positions = {(r.x, r.y): r for r in robots}
        print("\n" + "=" * (self.width * 2 + 1))
        for y in range(self.height):
            row_chars = []
            for x in range(self.width):
                if (x, y) in robot_positions:
                    row_chars.append(f"\033[92m{robot_positions[(x, y)].icon()}\033[0m")
                else:
                    cell = self.grid[y][x]
                    color = {
                        CellType.WALL: "\033[91m#\033[0m",
                        CellType.SHELF: "\033[93mS\033[0m",
                        CellType.CHARGER: "\033[96mC\033[0m",
                        CellType.LOADING: "\033[95mL\033[0m",
                        CellType.DELIVERY: "\033[94mD\033[0m",
                        CellType.EMPTY: ".",
                    }[cell]
                    row_chars.append(color)
            print(" ".join(row_chars))
        print("=" * (self.width * 2 + 1))
