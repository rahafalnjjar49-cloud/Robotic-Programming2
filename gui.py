"""
gui.py
------
Extension Track C: Graphical Visualization, implemented with Tkinter
(built into the Python standard library -- no extra install needed, which
makes it the safest choice for running directly in VS Code).

Usage:
    python main.py --gui
"""

import tkinter as tk

from environment import CellType
from robot import RobotState

CELL_SIZE = 36

COLORS = {
    CellType.EMPTY: "#f5f5f5",
    CellType.WALL: "#333333",
    CellType.SHELF: "#c9a35a",
    CellType.CHARGER: "#7fd1ff",
    CellType.LOADING: "#ffd27f",
    CellType.DELIVERY: "#9ef5a0",
}

# Short letter shown on top of each special cell, and the legend text
CELL_LABELS = {
    CellType.SHELF: ("S", "Shelf / رف تخزين"),
    CellType.CHARGER: ("C", "Charging station / محطة شحن"),
    CellType.LOADING: ("L", "Loading station (pickup) / محطة تحميل"),
    CellType.DELIVERY: ("D", "Delivery station / محطة تسليم"),
}

ROBOT_COLORS = ["#e74c3c", "#3498db", "#9b59b6", "#e67e22", "#1abc9c", "#f39c12"]

STATE_COLORS = {
    "Idle": "#7f8c8d",
    "Moving": "#27ae60",
    "Loading": "#f39c12",
    "Delivering": "#2980b9",
    "Charging": "#16a085",
    "Waiting": "#c0392b",
}


class WarehouseGUI:
    def __init__(self, simulation, tick_delay_ms=300):
        self.sim = simulation
        self.tick_delay_ms = tick_delay_ms

        wh = simulation.warehouse
        self.root = tk.Tk()
        self.root.title("Autonomous Warehouse Robot Fleet Simulator")

        self.canvas = tk.Canvas(self.root, width=wh.width * CELL_SIZE,
                                 height=wh.height * CELL_SIZE, bg="white")
        self.canvas.pack(side=tk.LEFT)

        self.side_panel = tk.Frame(self.root, width=260)
        self.side_panel.pack(side=tk.RIGHT, fill=tk.Y)

        self.info_label = tk.Label(self.side_panel, justify=tk.LEFT, anchor="nw",
                                    font=("Consolas", 10))
        self.info_label.pack(fill=tk.X, padx=8, pady=(8, 4))

        self._build_legend()

        self._draw_static_grid()
        self.robot_items = {}

    # ------------------------------------------------------------------ #
    # Legend: explains every color/letter used on the map + robot badges
    # ------------------------------------------------------------------ #
    def _build_legend(self):
        legend_frame = tk.LabelFrame(self.side_panel, text="Legend / دليل الرموز",
                                      font=("Consolas", 9, "bold"), padx=6, pady=6)
        legend_frame.pack(fill=tk.X, padx=8, pady=4)

        def row(color, text, is_circle=False):
            r = tk.Frame(legend_frame)
            r.pack(fill=tk.X, pady=1)
            swatch = tk.Canvas(r, width=16, height=16, highlightthickness=0)
            if is_circle:
                swatch.create_oval(1, 1, 15, 15, fill=color, outline="black")
            else:
                swatch.create_rectangle(0, 0, 16, 16, fill=color, outline="#999999")
            swatch.pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(r, text=text, font=("Consolas", 8), anchor="w",
                     justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X)

        for cell_type, (letter, label_text) in CELL_LABELS.items():
            row(COLORS[cell_type], f"{letter} = {label_text}")

        tk.Frame(legend_frame, height=1, bg="#cccccc").pack(fill=tk.X, pady=4)
        row("#e74c3c", "Robot (colored circle, carries a 📦 badge\nwhile transporting a package)", is_circle=True)

    def _draw_static_grid(self):
        wh = self.sim.warehouse
        for y in range(wh.height):
            for x in range(wh.width):
                cell = wh.grid[y][x]
                color = COLORS[cell]
                self.canvas.create_rectangle(
                    x * CELL_SIZE, y * CELL_SIZE,
                    (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                    fill=color, outline="#dddddd")
                if cell in CELL_LABELS:
                    letter, _ = CELL_LABELS[cell]
                    self.canvas.create_text(
                        x * CELL_SIZE + CELL_SIZE / 2, y * CELL_SIZE + CELL_SIZE / 2,
                        text=letter, fill="#3a3a3a", font=("Arial", 12, "bold"))

    # ------------------------------------------------------------------ #
    # Robots: colored circle + name, plus a small package badge whenever
    # the robot is actually carrying a package (task phase == "DELIVER",
    # i.e. it already picked it up and is on its way to the destination).
    # ------------------------------------------------------------------ #
    def _draw_robots(self):
        for item_id in self.robot_items.values():
            self.canvas.delete(item_id)
        self.robot_items.clear()

        for i, r in enumerate(self.sim.robots):
            color = ROBOT_COLORS[i % len(ROBOT_COLORS)]
            x0 = r.x * CELL_SIZE + 4
            y0 = r.y * CELL_SIZE + 4
            x1 = (r.x + 1) * CELL_SIZE - 4
            y1 = (r.y + 1) * CELL_SIZE - 4

            carrying = bool(r.current_task and r.current_task.phase == "DELIVER")

            # subtle red outline while carrying, to be visible even without the badge
            outline_color = "#8b3a00" if carrying else "black"
            outline_width = 3 if carrying else 1

            oval = self.canvas.create_oval(x0, y0, x1, y1, fill=color,
                                            outline=outline_color, width=outline_width)
            label = self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2 + (4 if carrying else 0),
                                             text=r.name, fill="white",
                                             font=("Arial", 8, "bold"))
            self.robot_items[f"{r.id}_oval"] = oval
            self.robot_items[f"{r.id}_label"] = label

            if carrying:
                # small brown "package" square badge on the top-right of the robot
                bx0, by0 = x1 - 12, y0 - 6
                bx1, by1 = x1 + 4, y0 + 8
                badge = self.canvas.create_rectangle(bx0, by0, bx1, by1,
                                                       fill="#8b5a2b", outline="black")
                badge_text = self.canvas.create_text((bx0 + bx1) / 2, (by0 + by1) / 2,
                                                       text="P", fill="white",
                                                       font=("Arial", 7, "bold"))
                self.robot_items[f"{r.id}_badge"] = badge
                self.robot_items[f"{r.id}_badge_text"] = badge_text

    def _update_info(self):
        lines = [f"Tick: {self.sim.tick}",
                 f"Deliveries: {self.sim.stats.deliveries_completed}",
                 f"Pending pkgs: {len(self.sim.scheduler.pending_packages)}",
                 "-" * 30]
        for r in self.sim.robots:
            carrying_mark = " [carrying 📦]" if (r.current_task and r.current_task.phase == "DELIVER") else ""
            lines.append(f"{r.name}: {r.state.value:<10} bat={r.battery.level:5.1f}%{carrying_mark}")
        self.info_label.config(text="\n".join(lines))

    def _tick(self):
        self.sim.step()
        self._draw_robots()
        self._update_info()
        self.root.after(self.tick_delay_ms, self._tick)

    def run(self):
        self._draw_robots()
        self._update_info()
        self.root.after(self.tick_delay_ms, self._tick)
        self.root.mainloop()
