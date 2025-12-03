import requests
import json
import os
import shutil
import numpy as np

BASE_URL = "http://127.0.0.1:5001/api"
TEMP_DIR = os.path.join("workspace", "temp_lanes")

def test_recursive():
    # 0. Clean up
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    # 1. Load Data
    print("1. Loading lane-0.npy...")
    payload = {"raw_files": ["lane-0.npy"], "raw_data_dir": "TEMP1"}
    requests.post(f"{BASE_URL}/load", json=payload)
    
    # 2. Split lane-0 -> lane-0, lane-0_1
    print("2. Splitting lane-0...")
    # Get nodes to find a split point
    resp = requests.get(f"{BASE_URL}/data")
    nodes = resp.json()['nodes']
    mid_id = nodes[len(nodes)//2][0]
    
    requests.post(f"{BASE_URL}/operation", json={
        "operation": "delete_points",
        "params": {"point_ids": [mid_id]}
    })
    
    # Unload to trigger save/split
    requests.post(f"{BASE_URL}/unload", json={"filename": "lane-0.npy"})
    
    # Check files
    files = os.listdir(TEMP_DIR)
    print(f"   Files after first split: {files}")
    if "lane-0_1.npy" not in files:
        print("FAILURE: lane-0_1.npy not found.")
        return

    # 3. Load lane-0_1.npy
    print("3. Loading lane-0_1.npy...")
    payload = {"raw_files": ["lane-0_1.npy"], "raw_data_dir": "workspace/temp_lanes"}
    # Note: raw_data_dir needs to point to where lane-0_1.npy is. It's in temp_lanes.
    # But the loader expects a path relative to 'lanes' or absolute.
    # Let's use absolute path logic or just copy it to TEMP1 for test simplicity?
    # Or better, use the 'saved_graph_dir' feature if implemented, or just rely on the fact that 
    # load_data checks temp_lanes first?
    # Actually, load_data checks raw_files in raw_data_dir.
    # If I pass raw_data_dir as absolute path to temp_lanes...
    abs_temp_dir = os.path.abspath(TEMP_DIR)
    payload["raw_data_dir"] = abs_temp_dir
    
    requests.post(f"{BASE_URL}/load", json=payload)
    
    # 4. Split lane-0_1 -> lane-0_1, lane-0_1_1
    print("4. Splitting lane-0_1...")
    resp = requests.get(f"{BASE_URL}/data")
    nodes = resp.json()['nodes']
    # Find nodes belonging to lane-0_1 (should be all loaded nodes since we only loaded that file)
    if len(nodes) < 3:
        print("Not enough nodes to split recursively.")
        return
        
    mid_id = nodes[len(nodes)//2][0]
    requests.post(f"{BASE_URL}/operation", json={
        "operation": "delete_points",
        "params": {"point_ids": [mid_id]}
    })
    
    # Unload lane-0_1.npy
    requests.post(f"{BASE_URL}/unload", json={"filename": "lane-0_1.npy"})
    
    # Check files
    files = os.listdir(TEMP_DIR)
    print(f"   Files after recursive split: {files}")
    
    if "lane-0_1_1.npy" in files:
        print("SUCCESS: lane-0_1_1.npy found.")
    else:
        print("FAILURE: lane-0_1_1.npy not found.")

if __name__ == "__main__":
    test_recursive()
