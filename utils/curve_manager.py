from collections import deque

import numpy as np
from scipy.interpolate import splprep, splev


class CurveManager:
    def __init__(self, data_manager, plot_manager, event_handler):
        self.data_manager = data_manager
        self.plot_manager = plot_manager
        self.event_handler = event_handler
        self.draw_points = []
        self.is_curve = False
        self.current_line = None
        self.show_debug_plot = False
        self.smoothing_weight = 1

    def add_draw_point(self, x, y):
        try:
            self.draw_points.append([x, y])
            self.update_draw_line()
        except Exception as e:
            print(f"Error adding draw point: {e}")

    def update_draw_line(self):
        if self.current_line:
            self.current_line.remove()
            self.current_line = None
        if len(self.draw_points) < 2:
            return
        points = np.array(self.draw_points)
        x, y = points[:, 0], points[:, 1]
        try:
            self.current_line = self.plot_manager.ax.plot(x, y, 'k-', alpha=0.5)[0]
            self.plot_manager.fig.canvas.draw_idle()
        except Exception as e:
            print(f"Error updating draw line: {e}")

    def finalize_draw(self, original_lane_id):
        if len(self.draw_points) < 2:
            self.clear_draw()
            return
        points = np.array(self.draw_points)
        try:
            previous_node_id = None
            new_node_ids = []
            for x, y in points:
                new_node_id = self.data_manager.add_node(x, y, original_lane_id)
                new_node_ids.append(new_node_id)
                if previous_node_id is not None:
                    self.data_manager.add_edge(previous_node_id, new_node_id)
                previous_node_id = new_node_id
            print(f"Finalized draw: Added {len(new_node_ids)} nodes and {len(new_node_ids) - 1} edges.")
        except Exception as e:
            print(f"Error finalizing draw: {e}")
        finally:
            self.clear_draw()
            self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)

    def clear_draw(self):
        self.draw_points = []
        if self.current_line:
            try:
                self.current_line.remove()
            except ValueError:
                pass
            self.current_line = None
        self.plot_manager.fig.canvas.draw_idle()

    def _get_node_coords(self, point_id):
        """Helper to get (x, y) for a point_id."""
        node_mask = (self.data_manager.nodes[:, 0] == point_id)
        if np.any(node_mask):
            return self.data_manager.nodes[node_mask][0, 1:3]  # [x, y]
        return None

    def _find_path(self, start_id, end_id):
        """Finds a path from start_id to end_id using bidirectional BFS.
        
        This function constructs a bidirectional adjacency list from the edges in
        self.data_manager. It performs a breadth-first search (BFS) to explore possible
        paths from start_id to end_id. If a valid path is found, it returns a list of
        point_ids representing the path; otherwise, it returns None.
        """
        if self.data_manager.edges.size == 0:
            return None

        # Create a bidirectional adjacency list
        adj = {}
        for from_id, to_id in self.data_manager.edges:
            from_id, to_id = int(from_id), int(to_id)
            adj.setdefault(from_id, []).append(to_id)
            adj.setdefault(to_id, []).append(from_id) # Add the reverse edge

        if start_id not in adj:
            return None  # Start node has no connections

        queue = deque([(start_id, [start_id])])  # (current_node, path_to_node)
        visited = {start_id}

        while queue:
            current_id, path = queue.popleft()

            if current_id == end_id:
                return path  # Found the path

            for neighbor_id in adj.get(current_id, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    new_path = path + [neighbor_id]
                    queue.append((neighbor_id, new_path))

        return None

    def clear_preview(self):
        """Removes the smoothing preview line."""
        if self.event_handler.smoothing_preview_line:
            try:
                self.event_handler.smoothing_preview_line.remove()
            except ValueError:
                pass
            self.event_handler.smoothing_preview_line = None
            self.plot_manager.fig.canvas.draw_idle()

    def preview_smooth(self, start_id, end_id):
        """Generates and draws a preview of the smoothed path."""
        self.clear_preview()

        path_ids = self._find_path(start_id, end_id)
        if not path_ids:
            self.event_handler.update_status("No forward/backward path found between nodes.")
            print(f"No forward path found from {start_id} to {end_id}")
            return

        self.event_handler.smoothing_path_ids = path_ids  # Store for apply_smooth

        new_points_xy = self._smooth_segment(path_ids, preview=True)
        if new_points_xy is None:
            self.event_handler.update_status("Smoothing failed.")
            return

        # Draw the preview line
        self.event_handler.smoothing_preview_line = self.plot_manager.ax.plot(
            new_points_xy[:, 0], new_points_xy[:, 1], 'b--', alpha=0.7, zorder=5
        )[0]
        self.plot_manager.fig.canvas.draw_idle()
        self.event_handler.update_status("Preview generated. Adjust sliders or 'Confirm Smooth'.")

    def apply_smooth(self):
        """Applies the smoothing to the data_manager.nodes array."""
        path_ids = self.event_handler.smoothing_path_ids
        if not path_ids:
            print("No path to apply smoothing to.")
            return

        # Get the final smoothed points
        new_points_xy = self._smooth_segment(path_ids, preview=False)
        if new_points_xy is None:
            self.event_handler.update_status("Smoothing failed to apply.")
            return

        if len(new_points_xy) != len(path_ids):
            print(f"Error: Point count mismatch. Path: {len(path_ids)}, Smoothed: {len(new_points_xy)}")
            return

        # Update nodes in data_manager
        nodes = self.data_manager.nodes
        for i, point_id in enumerate(path_ids):
            node_mask = (nodes[:, 0] == point_id)
            if np.any(node_mask):
                # Update x, y (cols 1, 2)
                nodes[node_mask, 1:3] = new_points_xy[i]

                # Update yaw (col 3)
                if i < len(new_points_xy) - 1:  # Not the last point
                    dx = new_points_xy[i + 1, 0] - new_points_xy[i, 0]
                    dy = new_points_xy[i + 1, 1] - new_points_xy[i, 1]
                    nodes[node_mask, 3] = np.arctan2(dy, dx)
                else:
                    # Last point: copy yaw from previous point
                    if i > 0:
                        prev_mask = (nodes[:, 0] == path_ids[i - 1])
                        nodes[node_mask, 3] = nodes[prev_mask, 3]

        # Save to history
        self.data_manager.history.append((self.data_manager.nodes.copy(), self.data_manager.edges.copy()))
        self.data_manager.redo_stack = []

        # Redraw the main plot
        self.plot_manager.selected_indices = []
        self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)

    def straighten_segment(self, selected_indices, lane_id, start_idx, end_idx):
        try:
            new_points = self._smooth_segment(selected_indices, lane_id, start_idx, end_idx, preview=False)
            if new_points is None:
                return []

            selected_indices = sorted(selected_indices)
            start_pos = selected_indices.index(start_idx)
            end_pos = selected_indices.index(end_idx)
            if start_pos > end_pos:
                start_idx, end_idx = end_idx, start_idx
                start_pos, end_pos = end_pos, start_pos
            segment_indices = selected_indices[start_pos:end_pos + 1]

            if len(new_points) != len(segment_indices):
                print(f"Warning: Expected {len(segment_indices)} new points, got {len(new_points)}")
                return []

            self.data_manager.data[segment_indices, 0:2] = new_points

            for i, idx in enumerate(segment_indices):
                if i < len(new_points) - 1:
                    dx = new_points[i + 1, 0] - new_points[i, 0]
                    dy = new_points[i + 1, 1] - new_points[i, 1]
                    self.data_manager.data[idx, 2] = np.arctan2(dy, dx)
                else:
                    self.data_manager.data[idx, 2] = self.data_manager.data[segment_indices[-2], 2] if len(
                        segment_indices) > 1 else 0.0

            self.data_manager.data[segment_indices, -1] = lane_id
            self.data_manager.history.append(self.data_manager.data.copy())
            self.data_manager.redo_stack = []
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(self.data_manager.data)
            return segment_indices
        except Exception as e:
            print(f"Error straightening segment: {e}")
            return []

    def _smooth_segment(self, path_ids, preview=False):
        """Calculate smoothed points for a given path of IDs.
        
        This function retrieves the (x, y) coordinates for the specified path IDs and
        identifies adjacent points that are not part of the path. It constructs a
        fitting points array and applies spline interpolation to generate smoothed
        coordinates, ensuring the original start and end points are preserved. The
        function also handles cases where there are insufficient points or identical
        coordinates.
        
        Args:
            path_ids (list): A list of IDs representing the path to be smoothed.
            preview (bool): A flag indicating whether to preview the smoothing process.
        
        Returns:
            np.ndarray: An array of smoothed points, or None if smoothing cannot be performed.
        """
        if len(path_ids) < 2:
            print("Need at least 2 points to smooth")
            return None

            # 1. Get (x, y) coordinates for the path
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

        # 2. Find adjacent points (prev and next)
        #    This looks for nodes connected to the path's ends,
        #    but are not part of the path itself.
        prev_point, next_point = None, None
        start_id = path_ids[0]
        end_id = path_ids[-1]

        # Build bidirectional adjacency list
        adj = {}
        for from_id, to_id in self.data_manager.edges:
            from_id, to_id = int(from_id), int(to_id)
            adj.setdefault(from_id, []).append(to_id)
            adj.setdefault(to_id, []).append(from_id)

        # Find 'prev_point'
        if start_id in adj:
            for neighbor_id in adj[start_id]:
                if neighbor_id != path_ids[1]:  # Not the next point in the path
                    prev_point = self._get_node_coords(neighbor_id)
                    break

        # Find 'next_point'
        if end_id in adj:
            for neighbor_id in adj[end_id]:
                if neighbor_id != path_ids[-2]:  # Not the previous point in the path
                    next_point = self._get_node_coords(neighbor_id)
                    break

        # 3. Build fitting_points and weights
        fitting_points = points.copy()
        weights = np.ones(len(fitting_points)) * self.smoothing_weight

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

        # 4. Run spline math
        try:
            x, y = fitting_points[:, 0], fitting_points[:, 1]

            if len(np.unique(x)) < 2 and len(np.unique(y)) < 2:
                print("Cannot smooth a path of identical points.")
                return points  # Return original points

            distances = np.sqrt(np.sum(np.diff(fitting_points, axis=0) ** 2, axis=1))
            u = np.zeros(len(fitting_points))
            u[1:] = np.cumsum(distances)
            u = u / u[-1] if u[-1] > 0 else np.linspace(0, 1, len(fitting_points))

            smoothing_factor = len(points) * self.plot_manager.slider_smooth.val
            if smoothing_factor < 0.1: smoothing_factor = 0.1

            tck, u_fitted = splprep([x, y], u=u, s=smoothing_factor, k=3, w=weights)

            u_start_segment = u[segment_start_in_fitting]
            u_end_segment = u[segment_end_in_fitting]

            num_new_points = len(path_ids)  # Use original path length
            u_fine = np.linspace(u_start_segment, u_end_segment, num_new_points)

            x_smooth, y_smooth = splev(u_fine, tck)
            new_points = np.stack((x_smooth, y_smooth), axis=1)

            # Re-assert exact start/end points
            new_points[0] = original_start_point
            new_points[-1] = original_end_point

            return new_points

        except ValueError as e:
            print(f"Spline fitting failed: {e}")
            return None