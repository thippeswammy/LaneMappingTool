import numpy as np
import math

def angle_diff(a, b):
    """Calculates the smallest difference between two angles in radians."""
    diff = b - a
    while diff <= -math.pi:
        diff += 2 * math.pi
    while diff > math.pi:
        diff -= 2 * math.pi
    return diff

def is_pi_crossing(yaw1, yaw2):
    """Checks if the difference is due to crossing the PI boundary."""
    return abs(angle_diff(yaw1, yaw2)) < 0.1 and abs(yaw1 - yaw2) > 6.0

def get_distance(n1, n2):
    """Calculates Euclidean distance between two nodes."""
    dx = n1[1] - n2[1] # x is index 1
    dy = n1[2] - n2[2] # y is index 2
    return math.sqrt(dx*dx + dy*dy)

def local_curvature(yaws_arr, idx, window=5):
    """Estimates local curvature (change in yaw) around a point."""
    start = max(0, idx - window)
    end = min(len(yaws_arr), idx + window + 1)
    
    diffs = []
    for i in range(start, end - 1):
        d = abs(angle_diff(yaws_arr[i], yaws_arr[i+1]))
        if d < 1.0: # Filter out jumps for curvature estimation
            diffs.append(d)
    
    if not diffs:
        return 0.0
    return np.mean(diffs)

def detect_anomalies(nodes):
    """
    Detects yaw anomalies in the node list.
    
    Args:
        nodes (np.array): Array of nodes [id, x, y, yaw, zone, width, indicator]
        
    Returns:
        list: List of anomaly dictionaries {index, id, type, current_yaw, prev_yaw}
    """
    if nodes.size == 0:
        return []

    yaws = nodes[:, 3] # Yaw is index 3
    ids = nodes[:, 0]  # ID is index 0
    
    anomalies = []
    
    # Thresholds
    ZERO_DIFF_THRESH = 0.0001
    CURVE_THRESH = 0.003
    JUMP_THRESH = 0.5 
    DISCONTINUITY_THRESH = 2.0 # Meters
    
    for i in range(1, len(nodes)):
        curr_yaw = yaws[i]
        prev_yaw = yaws[i-1]
        
        # Check for spatial discontinuity FIRST
        dist = get_distance(nodes[i], nodes[i-1])
        if dist > DISCONTINUITY_THRESH:
            # Valid jump, skip anomaly detection for this transition
            continue
            
        diff = angle_diff(prev_yaw, curr_yaw)
        wrapped_diff = abs(diff)
        
        # Check 1: Zero Diff on Curve
        if wrapped_diff < ZERO_DIFF_THRESH:
            curvature = local_curvature(yaws, i)
            if curvature > CURVE_THRESH:
                anomalies.append({
                    'index': int(i),
                    'id': int(ids[i]),
                    'type': 'ZERO_DIFF',
                    'yaw': float(curr_yaw),
                    'prev_yaw': float(prev_yaw),
                    'info': f"Diff: {wrapped_diff:.6f}, Curv: {curvature:.6f}"
                })
                continue
                
        # Check 2: Large Corrective Jump
        # If previous was zero diff (or very small) and this is a big jump
        # Check if the jump is "corrective" (returning to flow) or just a sharp turn
        if wrapped_diff > JUMP_THRESH and not is_pi_crossing(prev_yaw, curr_yaw):
            # Inspect previous node for zero-diff context (simplified)
            if i > 1:
                prev_diff = abs(angle_diff(yaws[i-2], yaws[i-1]))
                if prev_diff < ZERO_DIFF_THRESH:
                     anomalies.append({
                        'index': int(i),
                        'id': int(ids[i]),
                        'type': 'JUMP',
                        'yaw': float(curr_yaw),
                        'prev_yaw': float(prev_yaw),
                        'info': f"Jump after zero-diff. Diff: {wrapped_diff:.4f}"
                    })

    return anomalies

def fix_anomalies(nodes):
    """
    Fixes detected anomalies in the nodes array.
    Returns the fixed nodes and a report of changes.
    """
    fixed_nodes = nodes.copy()
    anomalies = detect_anomalies(fixed_nodes)
    
    if not anomalies:
        # User requested: Set all zones to 0 even if no anomalies? 
        # Or only if anomalies found? The phrasing "on the fix Issues then set..." suggests it's part of the fix action.
        # But if the button is "Fix Issues" and it's disabled when 0 anomalies...
        # However, to be safe, let's reset zones anyway if this function is called.
        fixed_nodes[:, 4] = 0
        return fixed_nodes, "No yaw anomalies found, but Zones reset to 0."
    
    # Reset all Zones to 0 as requested
    fixed_nodes[:, 4] = 0
    
    ids = fixed_nodes[:, 0]
    
    report = []
    change_count = 0
    
    # We fix iteratively, but since detection depends on neighbors, 
    # a simple pass might miss some "jumps" that only look like jumps because of prev error.
    # However, our linear interpolation usually fixes the whole sequence.
    
    # Map indices to fix
    indices_to_fix = sorted([a['index'] for a in anomalies])
    
    # We need to group consecutive anomalies to interpolate correctly
    # But simple per-node interpolation from nearest *valid* neighbors works too
    
    for idx_to_fix in indices_to_fix:
        # Find nearest valid previous neighbor (backwards)
        prev_valid_idx = -1
        for i in range(idx_to_fix - 1, -1, -1):
            # Stop if we hit a spatial discontinuity
            if get_distance(fixed_nodes[i], fixed_nodes[i+1]) > 2.0:
                break # Cannot use neighbors across discontinuity
                
            if i not in indices_to_fix:
                prev_valid_idx = i
                break
        
        # Find nearest valid next neighbor (forwards)
        next_valid_idx = -1
        for i in range(idx_to_fix + 1, len(fixed_nodes)):
            # Stop if we hit a spatial discontinuity
            # Note: checking distance between i-1 and i. 
            # If we are at i=idx_to_fix+1, we check distance (idx_to_fix, idx_to_fix+1).
            # If that is discontinuous, we can't use this neighbor.
            if i > idx_to_fix: 
                 if get_distance(fixed_nodes[i-1], fixed_nodes[i]) > 2.0:
                    break
            
            if i not in indices_to_fix:
                next_valid_idx = i
                break
        
        # Interpolate
        old_yaw = fixed_nodes[idx_to_fix, 3]
        new_yaw = old_yaw
        method = "SKIPPED"
        
        if prev_valid_idx != -1 and next_valid_idx != -1:
            # Linear interpolation
            yaw1 = fixed_nodes[prev_valid_idx, 3]
            yaw2 = fixed_nodes[next_valid_idx, 3]
            
            # Handle wrap around for interpolation
            d = angle_diff(yaw1, yaw2)
            
            # Ratio of distances or just indices? Indices is simpler and usually sufficient for dense graphs
            total_steps = next_valid_idx - prev_valid_idx
            curr_step = idx_to_fix - prev_valid_idx
            ratio = curr_step / total_steps
            
            interpolated_diff = d * ratio
            target_yaw = yaw1 + interpolated_diff
            
            # Wrap result to -pi, pi
            if target_yaw > math.pi: target_yaw -= 2*math.pi
            if target_yaw <= -math.pi: target_yaw += 2*math.pi
            
            new_yaw = target_yaw
            method = "INTERP"
            
        elif prev_valid_idx != -1:
            # Copy prev
            new_yaw = fixed_nodes[prev_valid_idx, 3]
            method = "COPY_PREV"
            
        elif next_valid_idx != -1:
            # Copy next
            new_yaw = fixed_nodes[next_valid_idx, 3]
            method = "COPY_NEXT"
            
        # Apply fix
        fixed_nodes[idx_to_fix, 3] = new_yaw
        
        report.append({
            'id': int(ids[idx_to_fix]),
            'old_yaw': float(old_yaw),
            'new_yaw': float(new_yaw),
            'method': method
        })
        change_count += 1
        
    report.append({'id': -1, 'info': 'All Zones reset to 0'})
    return fixed_nodes, report

def get_yaw_profile(nodes):
    """
    Returns lists of [index, yaw] for plotting.
    Also returns discontinuity indices.
    """
    if nodes.size == 0:
        return [], []
        
    yaws = nodes[:, 3].tolist()
    ids = nodes[:, 0].tolist()
    
    curvatures = []
    diffs = []
    discontinuities = []
    
    for i in range(len(nodes)):
        # Curvature
        curv = local_curvature(nodes[:, 3], i)
        curvatures.append(float(curv))
        
        # Diff (backward)
        if i > 0:
            d = abs(angle_diff(nodes[i-1, 3], nodes[i, 3]))
             # Check discontinuity
            if get_distance(nodes[i], nodes[i-1]) > 2.0:
                discontinuities.append(i)
                d = 0 # Mask large diff at discontinuity
            diffs.append(float(d))
        else:
            diffs.append(0.0)

    return {
        'yaws': yaws,
        'ids': ids,
        'curvatures': curvatures,
        'diffs': diffs,
        'discontinuities': discontinuities
    }
