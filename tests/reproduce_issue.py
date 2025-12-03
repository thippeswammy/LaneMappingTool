import requests
import json
import os
import shutil
import numpy as np

BASE_URL = "http://127.0.0.1:5001/api"
TEMP_DIR = os.path.join("workspace", "temp_lanes")

def reproduce():
    # 0. Clean up
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    # 1. Load Data
    print("1. Loading lane-0.npy...")
    payload = {"raw_files": ["lane-0.npy"], "raw_data_dir": "TEMP1"}
    resp = requests.post(f"{BASE_URL}/load", json=payload)
    data = resp.json()
    nodes = data['nodes']
    initial_count = len(nodes)
    print(f"   Loaded {initial_count} nodes.")
    
    # 2. Break Link
    mid_node = nodes[initial_count // 2]
    mid_id = mid_node[0]
    print(f"2. Deleting point at node {mid_id} (Ctrl+Right Click)...")
    requests.post(f"{BASE_URL}/operation", json={
        "operation": "delete_points",
        "params": {"point_ids": [mid_id]}
    })
    
    # 3. Unload
    print("3. Unloading lane-0.npy...")
    requests.post(f"{BASE_URL}/unload", json={"filename": "lane-0.npy"})
    
    # 4. Check Temp Files
    files = os.listdir(TEMP_DIR)
    print(f"4. Temp files: {files}")
    
    lane0_path = os.path.join(TEMP_DIR, "lane-0.npy")
    if os.path.exists(lane0_path):
        pts = np.load(lane0_path)
        print(f"   lane-0.npy has {len(pts)} points.")
    
    # 5. Reload lane-0.npy
    print("5. Reloading lane-0.npy...")
    resp = requests.post(f"{BASE_URL}/load", json=payload)
    data = resp.json()
    new_nodes = data['nodes']
    print(f"   Reloaded {len(new_nodes)} nodes.")
    
    if len(new_nodes) == initial_count:
        print("FAILURE: Reloaded full original data (split failed or not saved).")
    else:
        print("SUCCESS: Reloaded partial data (split persisted).")

if __name__ == "__main__":
    reproduce()
