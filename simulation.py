import random

from robot import Robot, RobotState
from package import Package, Priority, PackageStatus
from path_planner import PathPlanner
from scheduler import Scheduler
from stats import StatisticsDashboard



DEADLOCK_WAIT_THRESHOLD = 3


class Simulation:

    def __init__(self, warehouse, num_robots=3, scheduler_strategy="nearest_robot",
                 package_spawn_chance=0.3, seed=None):
        self.warehouse = warehouse
        self.tick = 0
        self.rng = random.Random(seed)

        self.robots = self._spawn_robots(num_robots)
        self.scheduler = Scheduler(warehouse, strategy=scheduler_strategy)
        self.stats = StatisticsDashboard()

        self.package_spawn_chance = package_spawn_chance
        self.all_packages = []


    def _spawn_robots(self, num_robots):
        robots = []
        # place robots on the first `num_robots` charging stations if available,
        # otherwise scatter them on empty cells.
        spots = list(self.warehouse.charging_stations) or [(1, 1)]
        for i in range(num_robots):
            x, y = spots[i % len(spots)]
            robots.append(Robot(x, y))
        return robots

    def _maybe_spawn_package(self):
        if not self.warehouse.loading_stations or not self.warehouse.delivery_stations:
            return
        if self.rng.random() < self.package_spawn_chance:
            pickup = self.rng.choice(self.warehouse.loading_stations)
            destination = self.rng.choice(self.warehouse.delivery_stations)
            priority = self.rng.choice(list(Priority))
            pkg = Package(pickup, destination, priority)
            self.all_packages.append(pkg)
            self.scheduler.submit_package(pkg, tick=self.tick)

    
    def _handle_battery(self, robot):
        
        if robot.state == RobotState.CHARGING:
            robot.battery.charge()
            if robot.battery.is_full():
                robot.state = RobotState.IDLE
                robot.charging_target = None
                # resume interrupted task, if any
                if robot.current_task:
                    path = PathPlanner.find_path(self.warehouse, (robot.x, robot.y),
                                                  robot.current_task.target())
                    robot.path = path or []
                    robot.state = RobotState.MOVING
            return True  # battery logic handled this robot this tick

        if robot.needs_charging() and robot.charging_target is None:
            charger = self.warehouse.nearest_station(
                self.warehouse.charging_stations, robot.x, robot.y)
            if charger:
                robot.charging_target = charger
                robot.path = PathPlanner.find_path(self.warehouse, (robot.x, robot.y), charger) or []
                robot.state = RobotState.MOVING

        if robot.charging_target and (robot.x, robot.y) == robot.charging_target:
            robot.state = RobotState.CHARGING
            return True

        return False

    
    def _handle_task_progress(self, robot):
        if not robot.current_task or robot.path:
            return  # still travelling, or nothing to do

        task = robot.current_task
        if (robot.x, robot.y) != task.target():
            return

        if task.phase == "PICKUP":
            robot.state = RobotState.LOADING
            finished = task.advance_phase()
            path = PathPlanner.find_path(self.warehouse, (robot.x, robot.y), task.target())
            robot.path = path or []
            robot.state = RobotState.DELIVERING
        else:
            robot.state = RobotState.DELIVERING
            task.package.delivered_at_tick = self.tick
            finished = task.advance_phase()
            if finished:
                robot.deliveries_completed += 1
                self.stats.record_delivery(task.package)
                robot.current_task = None
                robot.state = RobotState.IDLE

    def _maybe_recover_from_deadlock(self, robot, reserved):
        
        if robot.consecutive_waits < DEADLOCK_WAIT_THRESHOLD or not robot.path:
            return

        target = robot.charging_target if robot.charging_target else (
            robot.current_task.target() if robot.current_task else None)
        if target is None:
            return

        avoid = reserved - {(robot.x, robot.y)}
        new_path = PathPlanner.find_path(self.warehouse, (robot.x, robot.y), target,
                                          avoid_cells=avoid)
        if new_path:
            robot.path = new_path
        
        robot.consecutive_waits = 0


    def step(self):
        
        self.tick += 1

        
        self._maybe_spawn_package()

        
        self.scheduler.assign(self.robots, tick=self.tick)

        
        reserved = set()
        for r in self.robots:
            reserved.add((r.x, r.y))  

        for robot in sorted(self.robots, key=lambda r: r.id):
            if self._handle_battery(robot):
                continue  

            if robot.path:
                next_cell = robot.path[0]
                if next_cell in reserved and next_cell != (robot.x, robot.y):
                    robot.state = RobotState.WAITING
                    robot.total_wait_ticks += 1
                    robot.consecutive_waits += 1
                    self._maybe_recover_from_deadlock(robot, reserved)
                    continue
                moved = robot.follow_path_step(self.warehouse, reserved)
                if moved:
                    robot.consecutive_waits = 0
                    reserved.discard((robot.x, robot.y))  
                    reserved.add((robot.x, robot.y))       
                else:
                    robot.consecutive_waits += 1
                    self._maybe_recover_from_deadlock(robot, reserved)
            elif robot.state not in (RobotState.CHARGING,):
                if not robot.current_task:
                    robot.state = RobotState.IDLE

            self._handle_task_progress(robot)

        
        self.stats.record_tick(self.robots)

    def run(self, ticks=100, render=False, delay=0.0):
        import time
        for _ in range(ticks):
            self.step()
            if render:
                self.warehouse.render(self.robots)
                if delay:
                    time.sleep(delay)
        self.stats.report()
