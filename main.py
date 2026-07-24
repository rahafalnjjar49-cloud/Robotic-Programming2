

import argparse

from environment import Warehouse
from simulation import Simulation


def parse_args():
    p = argparse.ArgumentParser(description="Autonomous Warehouse Robot Fleet Simulator")
    p.add_argument("--map", default="config/warehouse_map.json", help="path to warehouse JSON map")
    p.add_argument("--robots", type=int, default=3, help="number of robots")
    p.add_argument("--ticks", type=int, default=80, help="ticks to run in text mode")
    p.add_argument("--strategy", default="nearest_robot",
                    choices=["first_available", "nearest_robot",
                             "lowest_battery_avoidance", "priority_queue"],
                    help="task assignment strategy")
    p.add_argument("--spawn-chance", type=float, default=0.35,
                    help="probability of a new package spawning each tick")
    p.add_argument("--gui", action="store_true", help="launch the Tkinter GUI instead of text mode")
    p.add_argument("--seed", type=int, default=None, help="random seed for reproducibility")
    return p.parse_args()


def main():
    args = parse_args()

    warehouse = Warehouse.from_json(args.map)
    sim = Simulation(warehouse, num_robots=args.robots,
                      scheduler_strategy=args.strategy,
                      package_spawn_chance=args.spawn_chance,
                      seed=args.seed)

    if args.gui:
        from gui import WarehouseGUI
        WarehouseGUI(sim).run()
    else:
        sim.run(ticks=args.ticks, render=True, delay=0.05)


if __name__ == "__main__":
    main()
