from collections import deque
import numpy as np
from scipy.interpolate import splprep, splev

def _get_node_coords(nodes, point_id):
    """Helper to get (x, y) for a point_id from a nodes numpy array."""
    node_mask = (nodes[:, 0] == point_id)
    if np.any(node_mask):
        return nodes[node_mask][0, 1:3]  # [x, y]
    return None

def find_path(edges, start_id, end_id):
    """
    Finds a path from start_id to end_id using bidirectional BFS.
    This is a standalone utility function.
    """
    if edges.size == 0:
        return None

    adj = {}
    for from_id, to_id in edges:
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

def smooth_segment(nodes, edges, path_ids, smoothness, weight):
    """
    Calculate smoothed points for a given path of IDs.
    This is a standalone utility function.
    """
    if len(path_ids) < 3:
        print("Path too short for smoothing (needs >= 3 points)")
        return None

    points_xy = [_get_node_coords(nodes, pid) for pid in path_ids]
    points = np.array([p for p in points_xy if p is not None])
    
    # Check for duplicates or insufficient unique points
    if len(points) < 3:
         print("Insufficient valid points for smoothing")
         return None
         
    # Check for duplicate consecutive points which can crash splprep
    unique_points = np.unique(points, axis=0)
    if len(unique_points) < 3:
        print("Not enough unique points for B-spline")
        return None

    original_start_point = points[0]
    original_end_point = points[-1]

    prev_point, next_point = None, None
    start_id, end_id = path_ids[0], path_ids[-1]

    adj = {}
    for from_id, to_id in edges:
        from_id, to_id = int(from_id), int(to_id)
        adj.setdefault(from_id, []).append(to_id)
        adj.setdefault(to_id, []).append(from_id)

    if start_id in adj and len(path_ids) > 1:
        for neighbor_id in adj[start_id]:
            if neighbor_id != path_ids[1]:
                prev_point = _get_node_coords(nodes, neighbor_id)
                break

    if end_id in adj and len(path_ids) > 1:
        for neighbor_id in adj[end_id]:
            if neighbor_id != path_ids[-2]:
                next_point = _get_node_coords(nodes, neighbor_id)
                break

    fitting_points = points.copy()
    weights = np.ones(len(fitting_points)) * weight

    segment_start_idx = 0
    segment_end_idx = len(fitting_points) - 1
    HIGH_WEIGHT = 100

    if prev_point is not None:
        fitting_points = np.vstack([prev_point, fitting_points])
        weights = np.concatenate(([1], weights))
        segment_start_idx += 1
        segment_end_idx += 1

    if next_point is not None:
        fitting_points = np.vstack([fitting_points, next_point])
        weights = np.concatenate((weights, [1]))

    weights[segment_start_idx] = HIGH_WEIGHT
    weights[segment_end_idx] = HIGH_WEIGHT

    try:
        x, y = fitting_points[:, 0], fitting_points[:, 1]
        
        # Ensure we have enough points for k=3
        if len(fitting_points) <= 3:
             # Fallback to k=2 or k=1 if very few points, or just return None
             # But user asked for B-Spline which usually implies cubic (k=3)
             # If we added anchors, we might have enough.
             pass

        # Correct spline parameterization based on cumulative distance
        distances = np.sqrt(np.sum(np.diff(fitting_points, axis=0)**2, axis=1))
        
        # Handle case where all points are same location (distances all 0)
        if np.sum(distances) == 0:
             return None

        u = np.zeros(len(fitting_points))
        u[1:] = np.cumsum(distances)
        u /= u[-1]

        # Check for duplicate 'u' values which causes splprep to fail
        # This happens if two consecutive points are identical
        if len(np.unique(u)) < len(u):
             # Add tiny noise to duplicates to separate them
             u = u + np.random.normal(0, 1e-6, len(u))
             u = np.sort(u) # Re-sort just in case
             u /= u[-1] # Re-normalize

        tck, u_fitted = splprep([x, y], u=u, s=smoothness, k=3, w=weights)

        u_start = u[segment_start_idx]
        u_end = u[segment_end_idx]
        u_fine = np.linspace(u_start, u_end, len(path_ids))

        x_smooth, y_smooth = splev(u_fine, tck)
        new_points = np.vstack((x_smooth, y_smooth)).T

        new_points[0] = original_start_point
        new_points[-1] = original_end_point

        return new_points
    except Exception as e:
        print(f"Spline fitting failed: {e}")
        return None
