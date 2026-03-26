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

        # Draw the preview line
        self.event_handler.smoothing_preview_line = self.plot_manager.ax.plot(
            new_points_xy[:, 0], new_points_xy[:, 1], 'b--', alpha=0.7, zorder=5
        )[0]
        self.event_handler.smoothing_preview_points = self.plot_manager.ax.plot(
            new_points_xy[:, 0], new_points_xy[:, 1], 'rx', markersize=4, zorder=6
        )[0]
        self.plot_manager.fig.canvas.draw_idle()
        self.event_handler.update_status(f"Preview: {len(path_ids)} -> {len(new_points_xy)} pts. Adjust sliders or 'Confirm Smooth'.")

    def clear_preview(self):
        """Removes the smoothing preview line."""
        if self.event_handler.smoothing_preview_line:
            try:
                self.event_handler.smoothing_preview_line.remove()
            except ValueError:
                pass
            self.event_handler.smoothing_preview_line = None
            
        if hasattr(self.event_handler, 'smoothing_preview_points') and self.event_handler.smoothing_preview_points:
             try:
                 self.event_handler.smoothing_preview_points.remove()
             except ValueError:
                 pass
             self.event_handler.smoothing_preview_points = None
             
        self.plot_manager.fig.canvas.draw_idle()

    def apply_smooth(self):
        """Applies the smoothing to the data_manager.nodes array, replacing nodes if necessary."""
        path_ids = self.event_handler.smoothing_path_ids
        if not path_ids:
            print("No path to apply smoothing to.")
            return

        # Get the final smoothed points (no preview)
        new_points_xy = self._smooth_segment(path_ids, preview=False)
        if new_points_xy is None:
            self.event_handler.update_status("Smoothing failed to apply.")
            return

        # ---------------------------------------------------------
        # Logic to Replace Nodes (Handle Resampling)
        # ---------------------------------------------------------
        # Strategy:
        # 1. Update Start Node (path_ids[0]) to new_points_xy[0]
        # 2. Update End Node (path_ids[-1]) to new_points_xy[-1]
        # 3. Delete Intermediate Nodes (path_ids[1:-1])
        # 4. Create New Intermediate Nodes for new_points_xy[1:-1]
        # 5. Link Start -> New -> ... -> End
        # ---------------------------------------------------------

        try:
            start_id = path_ids[0]
            end_id = path_ids[-1]
            
            # 1. Update Start and End Coordinates
            self.data_manager.update_node(start_id, new_points_xy[0, 0], new_points_xy[0, 1])
            self.data_manager.update_node(end_id, new_points_xy[-1, 0], new_points_xy[-1, 1])
            
            # 2. Delete Intermediate Nodes
            # We must be careful not to break the graph before we reconnect, 
            # but standard delete_node might be too aggressive if we don't handle edges.
            # Ideally, we remove edges between start->...->end first.
            
            # Collect intermediate IDs
            intermediate_ids = path_ids[1:-1]
            
            # Remove edges along the old path
            for i in range(len(path_ids) - 1):
                u, v = path_ids[i], path_ids[i+1]
                self.data_manager.remove_edge(u, v)

            # Now delete intermediate nodes
            for pid in intermediate_ids:
                self.data_manager.remove_node(pid) # This cleans up any other edges they might have had (though usually none in a line)

            # 3. Create New Intermediate Nodes and Link
            prev_id = start_id
            lane_id = self.data_manager.get_node_lane_id(start_id) # Assume same lane
            
            # Loop through new intermediate points
            for i in range(1, len(new_points_xy) - 1):
                x, y = new_points_xy[i]
                new_node_id = self.data_manager.add_node(x, y, lane_id)
                self.data_manager.add_edge(prev_id, new_node_id)
                prev_id = new_node_id
            
            # Link final new node (or start if none) to end
            self.data_manager.add_edge(prev_id, end_id)

            # 4. Recalculate Yaw for the whole segment (Start -> ... -> End)
            # We need to traverse the new path to calculate yaw
            # Or just update it based on coordinates since we know the order
            # Let's simple traverse or list them.
            # The list of IDs in order is: [start_id] + [new_intermediate_ids...] + [end_id]
            # Since we just added them, getting IDs back is tricky unless we tracked them.
            
            # Re-fetch path to ensure we have correct IDs
            new_path_ids = self._find_path(start_id, end_id)
            if new_path_ids:
               self._recalculate_yaw_for_path(new_path_ids)

            # Save to history
            self.data_manager.history.append((self.data_manager.nodes.copy(), self.data_manager.edges.copy()))
            self.data_manager.redo_stack = []

            # Redraw
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
            self.event_handler.update_status(f"Smoothed & Resampled: {len(path_ids)} -> {len(new_points_xy)} nodes.")
            
        except Exception as e:
            print(f"Error applying smooth: {e}")
            self.event_handler.update_status(f"Error applying smooth: {e}")

    def _recalculate_yaw_for_path(self, path_ids):
        nodes = self.data_manager.nodes
        points = []
        # Extract points
        for pid in path_ids:
            mask = (nodes[:, 0] == pid)
            if np.any(mask):
                points.append(nodes[mask][0, 1:3])
        
        points = np.array(points)
        if len(points) < 2: return

        # Calc yaw
        yaws = np.zeros(len(points))
        # Forward difference (or central?) - Simple forward for now
        dirs = np.diff(points, axis=0)
        yaws[:-1] = np.arctan2(dirs[:, 1], dirs[:, 0])
        yaws[-1] = yaws[-2] # Last point gets prev yaw
        
        # Update
        for i, pid in enumerate(path_ids):
            mask = (nodes[:, 0] == pid)
            if np.any(mask):
                nodes[mask, 3] = yaws[i]

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
        """Calculate smoothed points using Context-Aware Spline + Resampling + Moving Average.
        
        Args:
            path_ids (list): IDs of the selected segment to smooth.
            preview (bool): If True, faster calculation (optional).
        
        Returns:
            np.ndarray: (N, 2) array of new X,Y coordinates.
        """
        if len(path_ids) < 2:
            return None

        # --- 1. Fetch Coordinates for Selection ---
        points_xy = []
        for pid in path_ids:
            coords = self._get_node_coords(pid)
            if coords is not None:
                points_xy.append(coords)
        points = np.array(points_xy)
        if len(points) < 2:
            return None

        # --- 2. Build Context (Neighbors) ---
        # We look for N neighbors BEFORE start and AFTER end
        CONTEXT_SIZE = 3
        
        # Helper to traverse graph
        def get_neighbors_chain(start_node, exclude_node, n=3):
            chain = []
            curr = start_node
            excl = exclude_node
            for _ in range(n):
                # Find neighbors of curr that are NOT excl
                adj = self._get_adj_nodes(curr)
                others = [x for x in adj if x != excl]
                if not others:
                    break
                # Heuristic: if multiple, define logic? 
                # For lanes, usually linear. Pick first 'other'.
                next_node = others[0]
                coords = self._get_node_coords(next_node)
                if coords is None: break
                
                chain.append((next_node, coords))
                excl = curr
                curr = next_node
            return chain

        # Predecessors (traverse backwards from start)
        # Note: direction is arbitrary in undirected graph. We just go away from selection.
        predecessors = get_neighbors_chain(path_ids[0], path_ids[1], n=CONTEXT_SIZE)
        # Successors (traverse forwards from end)
        successors = get_neighbors_chain(path_ids[-1], path_ids[-2], n=CONTEXT_SIZE)
        
        # Combine into Fitting Points
        # Predecessors are [immediate_prev, ..., far_prev]. Need to reverse to be [far, ..., immediate]
        prev_coords = [p[1] for p in reversed(predecessors)]
        next_coords = [p[1] for p in successors]
        
        fitting_points = points
        if prev_coords:
            fitting_points = np.vstack([prev_coords, fitting_points])
        if next_coords:
            fitting_points = np.vstack([fitting_points, next_coords])

        # --- 3. Set Weights ---
        # Selection and immediate neighbors = 1 (Low weight, allows smoothing)
        # Outermost Context = 100 (High weight, Anchors)
        
        weights = np.ones(len(fitting_points))
        HIGH_WEIGHT = 100
        
        # Set anchor weights if context exists
        if prev_coords:
            weights[0] = HIGH_WEIGHT # Furthest previous point
        else:
            weights[0] = HIGH_WEIGHT # If no context, lock start itself
            
        if next_coords:
            weights[-1] = HIGH_WEIGHT # Furthest next point
        else:
            weights[-1] = HIGH_WEIGHT # If no context, lock end itself

        # --- 4. Spline Fit ---
        try:
            x, y = fitting_points[:, 0], fitting_points[:, 1]
            if len(np.unique(x)) < 2 and len(np.unique(y)) < 2:
                return points

            # Arc-length parameterization
            distances = np.sqrt(np.sum(np.diff(fitting_points, axis=0) ** 2, axis=1))
            u = np.concatenate(([0], np.cumsum(distances)))
            u = u / u[-1] if u[-1] > 0 else np.linspace(0, 1, len(fitting_points))

            smoothing_factor = len(fitting_points) * self.plot_manager.slider_smooth.val
            if smoothing_factor < 0.1: smoothing_factor = 0.1 # Min smooth

            # Fit spline
            # k=3 cubic, or k=2 if few points?
            k = 3 if len(fitting_points) > 3 else 2
            tck, u_fitted = splprep([x, y], u=u, s=smoothing_factor, k=k, w=weights)
            
            # --- 5. Generate New Points (Resampled) ---
            # We need to evaluate the spline from the start of SELECTION to end of SELECTION.
            # Find u values corresponding to selection start/end indices in fitting_points
            
            sel_start_idx = len(prev_coords)
            sel_end_idx = len(fitting_points) - len(next_coords) - 1
            
            u_start = u[sel_start_idx]
            u_end = u[sel_end_idx]
            
            # Estimate Arc Length of the selection
            selection_dist = u[sel_end_idx] * np.sum(distances) # Rough approx? No, 'u' is normalized cumsum.
            # Better: Sum distances within selection
            # distances array index i corresponds to segment between i and i+1
            # indices of interest: sel_start_idx to sel_end_idx-1
            # BUT, we want Uniform Resampling.
            
            # Let's simple use uniform U distribution first, then map to distance?
            # Or just take many points and downsample?
            
            # Target spacing
            SPACING = 0.5 # meters
            
            # Total length of fitted spline subset
            # Not trivial to get exact length from tck. 
            # Approximation: Sum of linear distances of selection
            sel_linear_dist = np.sum(distances[sel_start_idx : sel_end_idx])
            
            num_points = int(max(2, sel_linear_dist / SPACING))
            
            u_fine = np.linspace(u_start, u_end, num_points)
            
            x_smooth, y_smooth = splev(u_fine, tck)
            new_points = np.stack((x_smooth, y_smooth), axis=1)

            # --- 6. Post-Process: Moving Average Filter ---
            # Reduces high frequency ripples
            if len(new_points) >= 3:
                new_points = self._moving_average(new_points, window=3)

            # Force Start/End alignment to be safe? 
            # In context-aware, we technically allow them to drift to match tangent.
            # But if we want to physically connect to existing nodes, we might need to snap?
            # Creating new nodes handles connectivity. But coordinates might jump slightly from 'prev_coords[-1]'.
            # If prev_coords exits, 'new_points[0]' should be close to 'prev_coords[-1]' (the one before selection).
            # No, 'points[0]' is the start of selection. 'prev_coords[-1]' is immediate neighbor.
            # We are replacing selection. 
            # The gap between 'prev_coords[-1]' and 'new_points[0]' depends on spline.
            # Since we included prev_coords in fit, it should be smooth.
            
            return new_points

        except Exception as e:
            print(f"Spline fitting failed: {e}")
            return None

    def _get_adj_nodes(self, node_id):
        adj = []
        node_id = int(node_id)
        for u, v in self.data_manager.edges:
            u, v = int(u), int(v)
            if u == node_id: adj.append(v)
            elif v == node_id: adj.append(u)
        return adj

    def _moving_average(self, points, window=3):
        # Apply MA to X and Y
        if window < 2: return points
        kernel = np.ones(window) / window
        
        # Pad edges to keep shape or use 'same'/'valid'?
        # We want to preserve endpoints generally, but smoothing them is also fine if anchored context handles it.
        # Let's use 'valid' and pad manually or 'mode=edge'.
        
        x = points[:, 0]
        y = points[:, 1]
        
        # Simple convolution with 'same' boundary
        x_smooth = np.convolve(x, kernel, mode='same')
        y_smooth = np.convolve(y, kernel, mode='same')
        
        # Fix boundaries (convolution distorts edges depending on padding)
        # 'same' with default zero padding is bad.
        # Let's just do weighted average of neighbors.
        
        # Better: simple loop for clarity/control
        res = points.copy()
        # half = window // 2
        # for i in range(len(points)):
        #     start = max(0, i - half)
        #     end = min(len(points), i + half + 1)
        #     res[i] = np.mean(points[start:end], axis=0)
            
        # Numpy vectorized
        pad_width = window // 2
        x_pad = np.pad(x, (pad_width, pad_width), mode='edge')
        y_pad = np.pad(y, (pad_width, pad_width), mode='edge')
        
        x_new = np.convolve(x_pad, kernel, mode='valid')
        y_new = np.convolve(y_pad, kernel, mode='valid')
        
        return np.stack((x_new, y_new), axis=1)