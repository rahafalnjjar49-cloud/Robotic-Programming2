"""
package.py
----------
Package: a parcel that must move from a pickup (loading station) to a
delivery station.
Task: the unit of work handed to a Robot by the Scheduler. A Task wraps a
Package plus its two legs (go pick it up, then deliver it) and tracks status.
"""

import itertools
from enum import Enum


class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class PackageStatus(Enum):
    WAITING = "Waiting"          # created, not yet assigned
    ASSIGNED = "Assigned"        # a robot is on the way to pick it up
    IN_TRANSIT = "In Transit"    # robot is carrying it to the destination
    DELIVERED = "Delivered"


class Package:
    _id_counter = itertools.count(1)

    def __init__(self, pickup, destination, priority=Priority.NORMAL):
        self.id = next(Package._id_counter)
        self.pickup = pickup            # (x, y)
        self.destination = destination  # (x, y)
        self.priority = priority
        self.status = PackageStatus.WAITING
        self.created_at_tick = None
        self.delivered_at_tick = None

    def __repr__(self):
        return (f"<Package #{self.id} {self.pickup}->{self.destination} "
                f"prio={self.priority.name} status={self.status.value}>")


class Task:
    """
    Wraps a Package into something a Robot executes.
    A Task has two phases:
      1. PICKUP  -> robot travels to package.pickup, then "loads" it
      2. DELIVER -> robot travels to package.destination, then "delivers" it
    """

    def __init__(self, package):
        self.package = package
        self.phase = "PICKUP"

    def target(self):
        return self.package.pickup if self.phase == "PICKUP" else self.package.destination

    def advance_phase(self):
        """Call when the robot reaches the current target."""
        if self.phase == "PICKUP":
            self.phase = "DELIVER"
            self.package.status = PackageStatus.IN_TRANSIT
            return False  # task not finished yet
        else:
            self.package.status = PackageStatus.DELIVERED
            return True  # task finished

    def __repr__(self):
        return f"<Task pkg=#{self.package.id} phase={self.phase}>"
