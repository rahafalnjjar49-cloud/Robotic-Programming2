class StatisticsDashboard:

    def __init__(self):
        self.tick_count = 0
        self.battery_samples = []          
        self.robot_busy_ticks = {}        
        self.robot_total_ticks = {}        
        self.delivery_times = []           
        self.collisions_avoided = 0
        self.deliveries_completed = 0

    def record_tick(self, robots):
        self.tick_count += 1
        if robots:
            avg_batt = sum(r.battery.level for r in robots) / len(robots)
            self.battery_samples.append(avg_batt)

        for r in robots:
            self.robot_total_ticks[r.id] = self.robot_total_ticks.get(r.id, 0) + 1
            if r.state.value != "Idle":
                self.robot_busy_ticks[r.id] = self.robot_busy_ticks.get(r.id, 0) + 1
            if r.state.value == "Waiting":
                self.collisions_avoided += 1

    def record_delivery(self, package):
        self.deliveries_completed += 1
        if package.created_at_tick is not None and package.delivered_at_tick is not None:
            self.delivery_times.append(package.delivered_at_tick - package.created_at_tick)

    def report(self):
        avg_battery = (sum(self.battery_samples) / len(self.battery_samples)
                        if self.battery_samples else 0)
        avg_delivery_time = (sum(self.delivery_times) / len(self.delivery_times)
                              if self.delivery_times else 0)

        print("\n" + "=" * 40)
        print(" SIMULATION STATISTICS")
        print("=" * 40)
        print(f"Ticks run              : {self.tick_count}")
        print(f"Deliveries completed   : {self.deliveries_completed}")
        print(f"Average delivery time  : {avg_delivery_time:.1f} ticks")
        print(f"Average battery level  : {avg_battery:.1f}%")
        print(f"Collisions avoided     : {self.collisions_avoided}")
        print("Robot utilization:")
        for rid, busy in self.robot_busy_ticks.items():
            total = self.robot_total_ticks.get(rid, 1)
            print(f"  Robot {rid}: {busy / total * 100:.1f}%")
        print("=" * 40)
