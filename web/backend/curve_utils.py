import numpy as np
from scipy.interpolate import splprep, splev
from collections import deque

class CurveUtils:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def _get_node_coords(self, point_id):
        """Helper to get (x, y) for a point_id."""
        node_mask = (self.data_manager.nodes[:, 0] == point_id)
        if np.any(node_mask):
            return self.data_manager.nodes[node_mask][0, 1:3]  # [x, y]
        return None

    def find_path(self, start_id, end_id):
        """Finds a path from start_id to end_id using bidirectional BFS."""
        if self.data_manager.edges.size == 0:
            return None

        # Create a bidirectional adjacency list
        adj = {}
        for from_id, to_id in self.data_manager.edges:
            from_id, to_id = int(from_id), int(to_id)
            adj.setdefault(from_id, []).append(to_id)
            adj.setdefault(to_id, []).append(from_id)

        if start_id not in adj:
            return None

        queue = deque([(start_id, [start_id])])
        visited = {start_id}

        while queue:
            current_id, path = queue.popleft()

            if current_id == end_id:
                return path

            for neighbor_id in adj.get(current_id, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    new_path = path + [neighbor_id]
                    queue.append((neighbor_id, new_path))

        return None

    def smooth_segment(self, path_ids, smoothness=1.0, weight=20):
        """Calculate smoothed points for a given path of IDs."""
        if len(path_ids) < 2:
            return None

        points_xy = []
        for pid in path_ids:
            coords = self._get_node_coords(pid)
            if coords is not None:
                points_xy.append(coords)
        points = np.array(points_xy)
        if len(points) < 2:
            return None

        original_start_point = points[0]
        original_end_point = points[-1]

        # Find adjacent points (prev and next)
        prev_point, next_point = None, None
        start_id = path_ids[0]
        end_id = path_ids[-1]

        adj = {}
        for from_id, to_id in self.data_manager.edges:
            from_id, to_id = int(from_id), int(to_id)
            adj.setdefault(from_id, []).append(to_id)
            adj.setdefault(to_id, []).append(from_id)

        if start_id in adj:
            for neighbor_id in adj[start_id]:
                if neighbor_id != path_ids[1]:
                    prev_point = self._get_node_coords(neighbor_id)
                    break

        if end_id in adj:
            for neighbor_id in adj[end_id]:
                if neighbor_id != path_ids[-2]:
                    next_point = self._get_node_coords(neighbor_id)
                    break

        fitting_points = points.copy()
        weights = np.ones(len(fitting_points)) * weight

        segment_start_in_fitting = 0
        segment_end_in_fitting = len(fitting_points) - 1
        HIGH_WEIGHT = 100

        if prev_point is not None:
            fitting_points = np.vstack([prev_point, fitting_points])
            weights = np.concatenate(([1], weights))
            segment_start_in_fitting += 1
            segment_end_in_fitting += 1

        if next_point is not None:
            fitting_points = np.vstack([fitting_points, next_point])
            weights = np.concatenate((weights, [1]))

        weights[segment_start_in_fitting] = HIGH_WEIGHT
        weights[segment_end_in_fitting] = HIGH_WEIGHT

        try:
            x, y = fitting_points[:, 0], fitting_points[:, 1]

            if len(np.unique(x)) < 2 and len(np.unique(y)) < 2:
                return points

            distances = np.sqrt(np.sum(np.diff(fitting_points, axis=0) ** 2, axis=1))
            u = np.zeros(len(fitting_points))
            u[1:] = np.cumsum(distances)
            u = u / u[-1] if u[-1] > 0 else np.linspace(0, 1, len(fitting_points))

            smoothing_factor = len(points) * smoothness
            if smoothing_factor < 0.1: smoothing_factor = 0.1

            tck, u_fitted = splprep([x, y], u=u, s=smoothing_factor, k=3, w=weights)

            u_start_segment = u[segment_start_in_fitting]
            u_end_segment = u[segment_end_in_fitting]

            num_new_points = len(path_ids)
            u_fine = np.linspace(u_start_segment, u_end_segment, num_new_points)

            x_smooth, y_smooth = splev(u_fine, tck)
            new_points = np.stack((x_smooth, y_smooth), axis=1)

            new_points[0] = original_start_point
            new_points[-1] = original_end_point

            return new_points

        except Exception as e:
            print(f"Spline fitting failed: {e}")
            return None

    def apply_smooth(self, path_ids, new_points_xy):
        """Applies the smoothing to the data_manager.nodes array."""
        if len(new_points_xy) != len(path_ids):
            return False

        nodes = self.data_manager.nodes
        for i, point_id in enumerate(path_ids):
            node_mask = (nodes[:, 0] == point_id)
            if np.any(node_mask):
                nodes[node_mask, 1:3] = new_points_xy[i]

                if i < len(new_points_xy) - 1:
                    dx = new_points_xy[i + 1, 0] - new_points_xy[i, 0]
                    dy = new_points_xy[i + 1, 1] - new_points_xy[i, 1]
                    nodes[node_mask, 3] = np.arctan2(dy, dx)
                else:
                    if i > 0:
                        prev_mask = (nodes[:, 0] == path_ids[i - 1])
                        nodes[node_mask, 3] = nodes[prev_mask, 3]

        self.data_manager.history.append((self.data_manager.nodes.copy(), self.data_manager.edges.copy()))
        self.data_manager.redo_stack = []
        self.data_manager._auto_save_backup()
        return True
