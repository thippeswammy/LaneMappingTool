import requests
import json
import os
import shutil
import numpy as np
import time
import sys

BASE_URL = "http://127.0.0.1:5001/api"
TEMP_LANES_DIR = os.path.join(os.getcwd(), "workspace", "temp_lanes")

def reproduce_undo():
    # 0. Clean up
    if os.path.exists(TEMP_LANES_DIR):
        try:
            shutil.rmtree(TEMP_LANES_DIR)
        except Exception as e:
            print(f"Warning: Could not clean temp dir: {e}")
    os.makedirs(TEMP_LANES_DIR, exist_ok=True)
    
    # Create a synthetic connected lane
    print("Creating synthetic connected lane...")
    nodes = []
    for i in range(100):
        # Point ID, X, Y, Yaw, Zone, Width, Indicator
        nodes.append([i, float(i), 0.0, 0.0, 0, 3.5, 0])
    nodes = np.array(nodes)
    np.save("synthetic_lane.npy", nodes)
    
    # 1. Load Data
    print("1. Loading synthetic_lane.npy...")
    response = requests.post(f"{BASE_URL}/load", json={
        "raw_files": ["synthetic_lane.npy"],
        "raw_data_dir": os.getcwd()
    })
    if response.status_code != 200:
        print(f"Failed to load data: {response.text}")
        sys.exit(1)

    # Check edges
    response = requests.get(f"{BASE_URL}/data")
    data = response.json()
    print(f"   Loaded {len(data['nodes'])} nodes and {len(data['edges'])} edges.")
    if len(data['edges']) == 0:
        print("   WARNING: No edges loaded! Split logic requires edges.")
        print("   Adding edges manually...")
        for i in range(99):
            requests.post(f"{BASE_URL}/operation", json={
                "operation": "add_edge",
                "params": {
                    "from_id": i,
                    "to_id": i+1
                }
            })
        print("   Edges added.")

    # 2. Split (Delete middle points)
    print("2. Splitting lane (deleting middle points)...")
    # Delete points 40-60 to create a split
    points_to_delete = list(range(40, 60))
    
    response = requests.post(f"{BASE_URL}/operation", json={
        "operation": "delete_points",
        "params": {
            "point_ids": points_to_delete
        }
    })
    
    if response.status_code != 200:
        print(f"Failed to delete points: {response.text}")
        sys.exit(1)
        
    # Check if split file exists
    files = os.listdir(TEMP_LANES_DIR)
    print(f"   Files after split: {files}")
    if not any("_1.npy" in f for f in files):
        print("WARNING: Split file not found! Split might not have happened.")

    # 3. Undo
    print("3. Undoing...")
    response = requests.post(f"{BASE_URL}/operation", json={
        "operation": "undo"
    })
    
    if response.status_code != 200:
        print(f"Failed to undo: {response.text}")
        sys.exit(1)

    # 4. Verify
    files = os.listdir(TEMP_LANES_DIR)
    print(f"   Files after undo: {files}")
    
    split_files = [f for f in files if "_1.npy" in f]
    if split_files:
        print(f"FAILURE: {split_files} still exists after undo.")
    else:
        print("SUCCESS: Split file is gone.")

if __name__ == "__main__":
    reproduce_undo()
