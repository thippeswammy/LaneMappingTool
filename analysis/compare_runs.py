import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from scipy.spatial import cKDTree

def load_data(run_dir):
    csv_path = os.path.join(run_dir, 'vehicle_data.csv')
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return None
    return pd.read_csv(csv_path)

def calculate_path_metrics(df):
    # Calculate accumulated distance
    dx = np.diff(df['x'])
    dy = np.diff(df['y'])
    dist = np.sqrt(dx**2 + dy**2)
    s = np.concatenate(([0], np.cumsum(dist)))
    df['s'] = s
    return df

def compare_runs(run1_path, run2_path, label1="Run 1", label2="Run 2"):
    df1 = load_data(run1_path)
    df2 = load_data(run2_path)
    
    if df1 is None or df2 is None: return

    df1 = calculate_path_metrics(df1)
    df2 = calculate_path_metrics(df2)
    
    # Comparison Logic: Spatial Alignment
    # We want to compare Steering at the same spatial location.
    # We'll treat df1 as the reference path.
    
    tree = cKDTree(df2[['x', 'y']].values)
    dists, indices = tree.query(df1[['x', 'y']].values)
    
    # Extract matched values
    df1['matched_steering_2'] = df2.iloc[indices]['steering_angle'].values
    df1['matched_speed_2'] = df2.iloc[indices]['speed'].values
    df1['spatial_diff'] = dists
    
    # Filter out bad matches (diverged paths)
    valid_mask = df1['spatial_diff'] < 1.0 # 1 meter tolerance
    df_valid = df1[valid_mask]
    
    plt.figure(figsize=(15, 10))
    
    # 1. Trajectory Map
    plt.subplot(2, 2, 1)
    plt.plot(df1['x'], df1['y'], label=label1, alpha=0.7)
    plt.plot(df2['x'], df2['y'], label=label2, alpha=0.7, linestyle='--')
    plt.title("Trajectory Comparison")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.axis('equal')
    plt.legend()
    plt.grid()
    
    # 2. Steering vs Distance
    plt.subplot(2, 2, 2)
    plt.plot(df_valid['s'], df_valid['steering_angle'], label=label1, alpha=0.7)
    plt.plot(df_valid['s'], df_valid['matched_steering_2'], label=label2 + " (Matched)", alpha=0.7, linestyle='--')
    plt.title("Steering Angle vs Distance")
    plt.xlabel("Distance Travelled (m)")
    plt.ylabel("Steering Angle")
    plt.legend()
    plt.grid()
    
    # 3. Steering Difference (Delta)
    plt.subplot(2, 2, 3)
    delta_steer = df_valid['steering_angle'] - df_valid['matched_steering_2']
    plt.plot(df_valid['s'], delta_steer, color='red', alpha=0.6)
    plt.title(f"Steering Difference ({label1} - {label2})")
    plt.xlabel("Distance (m)")
    plt.ylabel("Delta Steering")
    plt.grid()
    
    # 4. Speed Profile
    plt.subplot(2, 2, 4)
    plt.plot(df_valid['s'], df_valid['speed'], label=label1, alpha=0.7)
    plt.plot(df_valid['s'], df_valid['matched_speed_2'], label=label2, alpha=0.7, linestyle='--')
    plt.title("Speed Profile")
    plt.xlabel("Distance (m)")
    plt.ylabel("Speed")
    plt.legend()
    plt.grid()
    
    plt.tight_layout()
    plt.savefig("comparison_result.png")
    print("Comparison saved to comparison_result.png")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compare_runs.py <path_to_run1_folder> <path_to_run2_folder>")
        sys.exit(1)
        
    run1 = sys.argv[1]
    run2 = sys.argv[2]
    
    compare_runs(run1, run2, label1=os.path.basename(run1), label2=os.path.basename(run2))
