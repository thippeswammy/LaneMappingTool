import os
import numpy as np
import matplotlib.pyplot as plt

def load_csv(path):
    print(f"Loading CSV: {path}")
    try:
        # Load CSV using numpy. Skip header row.
        # Columns: timestamp,x,y,z,yaw,steering_angle,speed
        data = np.loadtxt(path, delimiter=',', skiprows=1)
        return data
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def calculate_distance(data):
    # Calculate cumulative distance traveled
    x = data[:, 1]
    y = data[:, 2]
    dx = np.diff(x)
    dy = np.diff(y)
    dist = np.sqrt(dx**2 + dy**2)
    s = np.concatenate(([0], np.cumsum(dist)))
    return s

def calculate_derivatives(data, time_col=0, val_col=5):
    # Calculate derivative of value with respect to time (e.g. steering rate)
    t = data[:, time_col]
    val = data[:, val_col]
    
    dt = np.diff(t)
    dval = np.diff(val)
    
    # Avoid division by zero
    dt[dt < 1e-6] = 1e-6
    
    deriv = dval / dt
    # Pad with 0 at the end to match length
    deriv = np.append(deriv, 0)
    return deriv

def count_steering_reversals(data, val_col=5):
    # Count how many times the steering rate changes sign (local extrema in steering)
    val = data[:, val_col]
    diffs = np.diff(val)
    # Signs of the differences
    signs = np.sign(diffs)
    # Remove zeros (no change) if any
    signs = signs[signs != 0]
    # Count sign changes
    reversals = np.count_nonzero(np.diff(signs))
    reversals = np.count_nonzero(np.diff(signs))
    return reversals

def find_oscillation_hotspots(data, window_size=50):
    # Sliding window to find count of reversals per window
    # Returns the index of the window with max reversals
    val = data[:, 5]
    diffs = np.diff(val)
    signs = np.sign(diffs)
    # Binary array where 1 is a reversal
    reversal_indices = np.where(np.diff(signs) != 0)[0]
    
    # We want density of reversals over distance or time indices
    # Let's just do a simple rolling count over the original indices
    n_samples = len(data)
    densities = []
    
    # Simple inefficient sliding window (optimize if slow, but fine for N<10k)
    max_density = 0
    max_idx = 0
    
    for i in range(0, n_samples - window_size, 10): # Stride 10
        start = i
        end = i + window_size
        # Count reversals in this range
        count = np.sum((reversal_indices >= start) & (reversal_indices < end))
        if count > max_density:
            max_density = count
            max_idx = start
            
    return max_idx, max_density

def main():
    base_dir = r"F:\RunningProjects\LaneMappingTool\analysis\recorded_data"
    original_path = os.path.join(base_dir, "original_run", "vehicle_data.csv")
    smoothed_path = os.path.join(base_dir, "smoothed_run", "vehicle_data.csv")
    
    output_dir = os.path.join(base_dir, "comparison_results")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    data_orig = load_csv(original_path)
    data_smooth = load_csv(smoothed_path)

    if data_orig is None or data_smooth is None:
        print("Failed to load data.")
        return

    # Calculate Distance
    s_orig = calculate_distance(data_orig)
    s_smooth = calculate_distance(data_smooth)

    # Calculate Steering Rate (deg/s or rad/s depending on raw units, assuming rad based on small values)
    # user data steering looks like -1.48, which is likely Radians (~-85 deg) or specific steering units.
    # If it is steering angle, let's assume it's comparable directly.
    steer_rate_orig = calculate_derivatives(data_orig, val_col=5)
    steer_rate_smooth = calculate_derivatives(data_smooth, val_col=5)

    reversals_orig = count_steering_reversals(data_orig, val_col=5)
    reversals_smooth = count_steering_reversals(data_smooth, val_col=5)

    dist_orig = s_orig[-1]
    dist_smooth = s_smooth[-1]

    # Statistics
    print("\n--- Statistics ---")
    print(f"Original Run Distance: {dist_orig:.2f} m")
    print(f"Smoothed Run Distance: {dist_smooth:.2f} m")
    
    print(f"Original Run Max Steering: {np.max(np.abs(data_orig[:, 5])):.4f}")
    print(f"Smoothed Run Max Steering: {np.max(np.abs(data_smooth[:, 5])):.4f}")
    
    print(f"Original Run Mean Abs Steering Rate: {np.mean(np.abs(steer_rate_orig)):.4f}")
    print(f"Smoothed Run Mean Abs Steering Rate: {np.mean(np.abs(steer_rate_smooth)):.4f}")
    
    print(f"Original Run Max Steering Rate: {np.max(np.abs(steer_rate_orig)):.4f}")
    print(f"Smoothed Run Max Steering Rate: {np.max(np.abs(steer_rate_smooth)):.4f}")

    print(f"Original Run Steering Reversals: {reversals_orig} ({(reversals_orig/dist_orig)*100:.2f} per 100m)")
    print(f"Smoothed Run Steering Reversals: {reversals_smooth} ({(reversals_smooth/dist_smooth)*100:.2f} per 100m)")

    # Localize Hotspots
    window_pts = 100 # roughly 100 samples ~ 5 seconds or 10-15 meters depending on speed
    hotspot_idx, hotspot_count = find_oscillation_hotspots(data_smooth, window_size=window_pts)
    
    hotspot_start_dist = s_smooth[hotspot_idx]
    hotspot_end_dist = s_smooth[min(hotspot_idx+window_pts, len(s_smooth)-1)]
    hotspot_x = data_smooth[hotspot_idx, 1]
    hotspot_y = data_smooth[hotspot_idx, 2]
    
    print(f"\n--- Hotspot Analysis ---")
    print(f"Highest Oscillation Area found at X={hotspot_x:.2f}, Y={hotspot_y:.2f}")
    print(f"Distance approx {hotspot_start_dist:.1f}m to {hotspot_end_dist:.1f}m along track")
    print(f"Contains {hotspot_count} reversals in {window_pts} samples (High Density!)")

    # Plotting
    plt.figure(figsize=(18, 12))

    # 1. Path Comparison (Mark Hotspot)
    plt.subplot(2, 2, 1)
    plt.plot(data_orig[:, 1], data_orig[:, 2], label='Original Run', alpha=0.5, color='blue')
    plt.plot(data_smooth[:, 1], data_smooth[:, 2], label='Smoothed Run', alpha=0.5, color='orange')
    # Highlight hotspot
    hotspot_segment = data_smooth[hotspot_idx:hotspot_idx+window_pts]
    plt.plot(hotspot_segment[:, 1], hotspot_segment[:, 2], color='red', linewidth=3, label='Max Oscillation Area')
    
    plt.title(f"Path Comparison (Red = Max Oscillation)")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.legend()
    plt.axis('equal')
    plt.grid(True)

    # 2. Steering Angle vs Distance (Zoomed in on Hotspot)
    plt.subplot(2, 2, 2)
    # Find corresponding range in Original run (approx by distance)
    mask_orig = (s_orig >= hotspot_start_dist - 10) & (s_orig <= hotspot_end_dist + 10)
    mask_smooth = (s_smooth >= hotspot_start_dist - 10) & (s_smooth <= hotspot_end_dist + 10)
    
    plt.plot(s_orig[mask_orig], data_orig[mask_orig, 5], label='Original', color='blue', marker='o', markersize=2)
    plt.plot(s_smooth[mask_smooth], data_smooth[mask_smooth, 5], label='Smoothed', color='orange', marker='x', markersize=2)
    
    plt.title(f"Steering Zoom: {hotspot_start_dist:.0f}m - {hotspot_end_dist:.0f}m")
    plt.xlabel("Distance (m)")
    plt.ylabel("Steering Angle")
    plt.legend()
    plt.grid(True)

    # 3. Steering Rate Full
    plt.subplot(2, 2, 3)
    plt.plot(s_orig, np.abs(steer_rate_orig), label='Original Run', alpha=0.4)
    plt.plot(s_smooth, np.abs(steer_rate_smooth), label='Smoothed Run', alpha=0.8)  # Make smooth more visible
    plt.title("Steering Rate Magnitude (Whole Track)")
    plt.xlabel("Distance (m)")
    plt.ylabel("|d(Steering)/dt|")
    plt.legend()
    plt.grid(True)

    # 4. Reversal Density Map (Rolling average)
    plt.subplot(2, 2, 4)
    # Compute rolling reversals for plot
    def rolling_reversals(data, w=100):
        res = []
        idxs = []
        for i in range(0, len(data)-w, 10):
            idx, count = find_oscillation_hotspots(data[i:i+w], window_size=w) # This function finds max, we need just count for *this* window
            # wait, reusing find_oscillation_hotspots is inefficient here.
            # redo:
            segment = data[i:i+w, 5]
            seg_diff = np.diff(segment)
            seg_signs = np.sign(seg_diff)
            seg_signs = seg_signs[seg_signs != 0]
            cnt = np.count_nonzero(np.diff(seg_signs))
            res.append(cnt)
            idxs.append(i)
        return idxs, res

    _, rev_counts_orig = rolling_reversals(data_orig, w=100)
    idxs_smooth, rev_counts_smooth = rolling_reversals(data_smooth, w=100)
    
    # Map indices to distances for x-axis
    dist_x = s_smooth[idxs_smooth]
    
    plt.plot(dist_x, rev_counts_smooth, label='Smoothed Reversal Density', color='red')
    # plt.plot(dist_x, rev_counts_orig, label='Original', alpha=0.3)
    plt.title("Oscillation Density (Reversals per ~10m)")
    plt.xlabel("Distance Along Path (m)")
    plt.ylabel("Reversals Count")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, "hotspot_analysis.png")
    plt.savefig(plot_path)
    print(f"\nSaved hotspot analysis to: {plot_path}")

if __name__ == "__main__":
    main()
