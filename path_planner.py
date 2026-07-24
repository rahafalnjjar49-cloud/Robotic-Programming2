

import heapq


class PathPlanner:

    @staticmethod
    def _heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def find_path(warehouse, start, goal, avoid_cells=None):
        
        avoid_cells = avoid_cells or set()

        if start == goal:
            return []

        open_set = [(0 + PathPlanner._heuristic(start, goal), 0, start)]
        came_from = {}
        g_score = {start: 0}
        visited = set()

        while open_set:
            _, cost, current = heapq.heappop(open_set)

            if current in visited:
                continue
            visited.add(current)

            if current == goal:
                return PathPlanner._reconstruct(came_from, current)

            for nx, ny in warehouse.neighbors(*current):
                neighbor = (nx, ny)
                if neighbor in avoid_cells and neighbor != goal:
                    continue
                tentative_g = cost + 1
                if tentative_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = tentative_g
                    priority = tentative_g + PathPlanner._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (priority, tentative_g, neighbor))
                    came_from[neighbor] = current

        return None  # no path found

    @staticmethod
    def _reconstruct(came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path[1:]  # drop the start cell itself
