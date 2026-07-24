"""
robot.py
--------
Defines the Robot itself plus two small helper classes: Battery and RobotState.

Design notes (why it's split this way):
- Battery is its own class so battery logic (drain, charge, threshold checks)
  is testable in isolation and can be swapped for a different model later.
- RobotState is an Enum representing the robot's finite-state machine.
- Robot composes Battery + a reference to a Path (list of coordinates) that
  the PathPlanner produced. The Robot does not compute paths itself -- that
  responsibility belongs to PathPlanner (separation of concerns).
"""

from enum import Enum


class RobotState(Enum):
    IDLE = "Idle"
    MOVING = "Moving"
    LOADING = "Loading"
    DELIVERING = "Delivering"
    CHARGING = "Charging"
    WAITING = "Waiting"


class Direction(Enum):
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)


class Battery:
    """Simple battery model: drains per move, recharges per tick while charging."""

    def __init__(self, capacity=100.0, drain_per_move=2.0, charge_per_tick=8.0,
                 low_threshold=28.0):
        self.capacity = capacity
        self.level = capacity
        self.drain_per_move = drain_per_move
        self.charge_per_tick = charge_per_tick
        self.low_threshold = low_threshold

    def drain(self):
        self.level = max(0.0, self.level - self.drain_per_move)

    def charge(self):
        self.level = min(self.capacity, self.level + self.charge_per_tick)

    def is_low(self):
        return self.level <= self.low_threshold

    def is_full(self):
        return self.level >= self.capacity

    def is_empty(self):
        return self.level <= 0.0


class Robot:
    """
    An autonomous warehouse robot.

    A Robot owns:
      - its position (x, y) and facing direction
      - a Battery
      - its current RobotState
      - the task it is currently executing (or None)
      - the path (list of (x, y) cells) it must still follow
    """

    _id_counter = 1

    def __init__(self, x, y, name=None, battery=None):
        self.id = Robot._id_counter
        Robot._id_counter += 1
        self.name = name or f"R{self.id}"

        self.x, self.y = x, y
        self.direction = Direction.EAST
        self.battery = battery or Battery()
        self.state = RobotState.IDLE

        self.current_task = None   # Task object
        self.path = []             # list of (x, y) remaining to travel
        self.charging_target = None
        self.consecutive_waits = 0  # ticks in a row spent WAITING (used for deadlock recovery)

        # simple stats used by the Statistics Dashboard extension
        self.deliveries_completed = 0
        self.total_moves = 0
        self.total_wait_ticks = 0

    def icon(self):
        arrows = {Direction.NORTH: "^", Direction.SOUTH: "v",
                  Direction.EAST: ">", Direction.WEST: "<"}
        return arrows[self.direction]

    def assign_task(self, task, path):
        """Attach a Task and the path the robot must follow to reach it."""
        self.current_task = task
        self.path = path
        self.state = RobotState.MOVING

    def follow_path_step(self, warehouse, occupied_cells):
        """
        Advance one cell along self.path if the next cell is free.
        Returns True if it moved, False if it had to wait (collision avoidance).
        `occupied_cells` is the set of (x, y) currently occupied by other robots
        this tick -- this is the simple "reservation" collision-avoidance scheme.
        """
        if not self.path:
            return False

        nx, ny = self.path[0]

        if (nx, ny) in occupied_cells or not warehouse.is_walkable(nx, ny):
            # Someone else is there (or will be) -> wait this tick, don't consume path
            self.state = RobotState.WAITING
            self.total_wait_ticks += 1
            return False

        # update facing direction
        dx, dy = nx - self.x, ny - self.y
        for d in Direction:
            if d.value == (dx, dy):
                self.direction = d
                break

        self.x, self.y = nx, ny
        self.path.pop(0)
        self.battery.drain()
        self.total_moves += 1
        self.state = RobotState.MOVING
        return True

    def needs_charging(self):
        return self.battery.is_low()

    def __repr__(self):
        return (f"<Robot {self.name} pos=({self.x},{self.y}) "
                f"state={self.state.value} battery={self.battery.level:.0f}%>")
