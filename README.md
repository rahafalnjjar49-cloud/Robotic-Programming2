Robotics Programming II – Final Project



## 1. Project Concept

This is a simulation project for a smart warehouse where multiple robots (three or more) operate autonomously. They pick up packages from loading stations and deliver them to delivery stations while avoiding collisions and managing their battery levels—proceeding to charging stations when necessary—all within a task scheduling framework controlled by a central scheduler.

The simulation operates in discrete time steps (ticks):
Each "tick" represents a single unit of time during which the robots move one step on the grid.

## 2. هيكلية المشروع (Architecture)

warehouse_simulator/
│
├── environment.py     # Warehouse: grid, walls, shelves, stations
├── robot.py            # Robot + Battery + RobotState + Direction
├── package.py          # Package + Task (package and its task)
├── path_planner.py     # PathPlanner: A* algorithm for path planning
├── scheduler.py         # Scheduler: task assignment strategies for robots
├── simulation.py        # Simulation: the main engine (main loop)
├── stats.py             # StatisticsDashboard (Extension D)
├── gui.py               # WarehouseGUI using Tkinter (Extension C)
├── main.py              # Entry point (text or GUI mode)
└── config/
    └── warehouse_map.json   # Warehouse map

This division applies the Separation of Concerns principle:
Each class is responsible for one thing only, which meets the "Software Architecture" and "Modular Design" requirements from the project description.

### مخطط الكلاسات 

```
Warehouse                     Robot                    Package
├── CellType (Enum)           ├── Direction (Enum)      ├── Priority (Enum)
├── grid[][]                  ├── RobotState (Enum)      ├── PackageStatus (Enum)
├── charging_stations[]       ├── Battery                └── id, pickup, destination
├── loading_stations[]        ├── x, y, direction
└── delivery_stations[]       ├── state, current_task
                               └── path[]

Task (يغلّف Package)     Scheduler                PathPlanner (A*)
├── phase: PICKUP/DELIVER  ├── strategy               └── find_path(warehouse, start, goal)
└── target()                ├── pending_packages[]
                             └── assign(robots)

Simulation                       StatisticsDashboard        WarehouseGUI
├── warehouse, robots[]           ├── deliveries_completed    └── Tkinter canvas +
├── scheduler, stats               ├── avg battery                لوحة معلومات حيّة
├── step()  -> tick واحد            └── collisions_avoided
└── run(ticks)
```

---

## 3. كيف تُلبّى متطلبات المشروع الإلزامية

Requirement	Where in the Code
2D environment configurable from JSON	environment.py -> Warehouse.from_json() and config/warehouse_map.json
≥ 3 robots with state/battery/direction	robot.py -> Robot, Battery, RobotState
Dynamic package system with priority	package.py -> Package, Priority + simulation.py -> _maybe_spawn_package
Task scheduling with multiple strategies	scheduler.py -> first_available / nearest_robot / lowest_battery_avoidance / priority_queue
Simulation engine with time steps	simulation.py -> Simulation.step()
A* Path Planning	path_planner.py -> PathPlanner.find_path()
Collision Avoidance (cell reservation system)	simulation.py -> step() builds a reserved set of occupied cells each "tick" and makes robots wait (WAITING) if the next cell is reserved
Battery Management (interrupt → charge → resume)	simulation.py -> _handle_battery()
Task assignment algorithm	scheduler.py -> assign()

### Two Extension Tracks Chosen

    C. Graphical Visualization via gui.py using Tkinter

    D. Statistics Dashboard via stats.py



---
## 4. Explanation of Each Algorithm
a) A* Path Planning (path_planner.py)

    Searches for the shortest path between two cells on the grid (4 directions: North/South/East/West).

    Uses heapq (as a Priority Queue) to select the cell with the lowest estimated cost f = g + h.

    h is the Manhattan Distance between the cell and the goal — an admissible heuristic because movement cost is always 1 on a 4-direction grid.

    Supports avoid_cells for replanning around temporarily reserved cells (used later if I wanted to activate "Replanning" as part of collision avoidance).

b) Collision Avoidance

I chose a Cell Reservation System + Waiting Policy:

    At the start of each tick, all cells currently occupied by robots are reserved.

    Each robot (in fixed order by id) tries to move to the next cell in its path.

    If the cell is reserved by another robot this tick, the robot transitions to WAITING state instead of moving, and this is recorded as a "collision avoided" in statistics.

    When a robot moves, the reservation set is updated immediately, so no two robots move to the same cell.

c) Battery Management — _handle_battery()

    Each move consumes a percentage of battery (drain_per_move).

    If the battery reaches a low threshold (low_threshold, default 20%) and the robot isn't already heading to a charging station:

        Its current task is interrupted (but not cancelled, it remains saved in current_task).

        A new path (A*) is planned to the nearest charging station.

    Upon reaching the station, the robot changes state to CHARGING and its battery increases each tick.

    When fully charged (100%), it returns to IDLE state and a new path (A*) is planned from its current location toward the goal of its previously interrupted task — meaning automatic resumption of work.

d) Task Assignment Algorithm (scheduler.py)

Supports 4 strategies (chosen via --strategy from command line):

    first_available: First idle robot available — the simplest.

    nearest_robot: Closest idle robot to the package (Manhattan distance) — default.

    lowest_battery_avoidance: Like nearest, but avoids robots with low battery if there's an alternative, to prevent exhausting them.

    priority_queue: Sorts packages by priority (URGENT > HIGH > NORMAL > LOW) first, then assigns to the nearest robot.

### 5. How to Run on VS Code (Step by Step)
a) Requirements

    Python 3.9 or newer (no external libraries needed — Tkinter is built into Python).

    On some Linux distributions, you may need to install python3-tk separately:
  ```bash
  sudo apt install python3-tk
  ```


### b) Steps to Run

    Open the warehouse_simulator folder in VS Code (File → Open Folder).

    Make sure VS Code is using the correct Python interpreter (Ctrl+Shift+P → Python: Select Interpreter).

    Open Terminal inside VS Code (Ctrl + `) and run:

    **Text Mode in terminal:**
   ```bash
   python main.py
   ```

   **Graphical Mode (Tkinter GUI):**
   ```bash
   python main.py --gui
   ```

   **Customize the simulation:**
   ```bash
   python main.py --gui --robots 4 --strategy priority_queue --spawn-chance 0.4
   python main.py --ticks 300 --strategy lowest_battery_avoidance --seed 42
   ```

4. You can also just press the ▶ Run button (top right of main.py file) directly.

### c) Command Line Options (main.py)
Option	Description	Default Value
--map	Path | to warehouse map JSON file	| config/warehouse_map.json
--robots|	Number of robots	 |3
--ticks | Number of simulation steps (text mode only)	| 80
--strategy |	Scheduling strategy |	nearest_robot
--spawn-chance |	Probability of new package spawning per tick	| 0.35
--gui	| Run with graphical interface	| Disabled
--seed |	Random seed for reproducible results |	Random

### d) Modifying the Warehouse Map
Open config/warehouse_map.json and modify the layout array — each character represents a cell type:
```
#  Wall        S  Shelf
C  Charging Station  L  Loading Station
D  Delivery Station  .  Empty cell

Important: Make sure each row has the same length as the width specified at the top of the file.
---

## 6. GUI Symbols
- Colored circle with a letter = robot (different color per robot).

- Light yellow S = Shelf.

- Light blue C = Charging Station.

- Light orange L = Loading Station.

- Light green D = Delivery Station.

- Side panel displays: tick number, number of deliveries, pending packages, and each robot's state/battery in real-time.
---

