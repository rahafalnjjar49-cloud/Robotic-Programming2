import heapq
import itertools

from package import Task, PackageStatus
from robot import RobotState
from path_planner import PathPlanner


class Scheduler:

    STRATEGIES = ("first_available", "nearest_robot",
                  "lowest_battery_avoidance", "priority_queue")

    def __init__(self, warehouse, strategy="nearest_robot"):
        self.warehouse = warehouse
        self.strategy = strategy
        self.pending_packages = []   
        self._counter = itertools.count()  

    def submit_package(self, package, tick=0):
        package.created_at_tick = tick
        self.pending_packages.append(package)

    def _idle_robots(self, robots):
        
        return [r for r in robots
                if r.state == RobotState.IDLE
                and r.current_task is None
                and r.charging_target is None]

    def _pick_robot(self, candidates, target):
        
        return min(candidates, key=lambda r: abs(r.x - target[0]) + abs(r.y - target[1]))

    def assign(self, robots, tick=0):
        
        if not self.pending_packages:
            return []

        assignments = []

        
        if self.strategy == "priority_queue":
            queue = sorted(self.pending_packages,
                            key=lambda p: (-p.priority.value, p.created_at_tick))
        else:
            queue = list(self.pending_packages)

        still_pending = []
        for package in queue:
            idle = self._idle_robots(robots)
            if not idle:
                still_pending.append(package)
                continue

            if self.strategy == "first_available":
                chosen = idle[0]
            elif self.strategy in ("nearest_robot", "priority_queue"):
                chosen = self._pick_robot(idle, package.pickup)
            elif self.strategy == "lowest_battery_avoidance":
                healthy = [r for r in idle if not r.needs_charging()]
                pool = healthy if healthy else idle
                chosen = self._pick_robot(pool, package.pickup)
            else:
                chosen = idle[0]

            path = PathPlanner.find_path(self.warehouse, (chosen.x, chosen.y), package.pickup)
            if path is None:
                still_pending.append(package)
                continue

            task = Task(package)
            chosen.assign_task(task, path)
            package.status = PackageStatus.ASSIGNED
            robots_state_update = chosen  # for clarity
            assignments.append((chosen, package))

        self.pending_packages = still_pending
        return assignments
