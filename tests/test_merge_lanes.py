import requests
import json
import os
import shutil
import numpy as np
import time

BASE_URL = "http://127.0.0.1:5001/api"
TEMP_DIR = os.path.join("web", "backend", "workspace", "temp_lanes")

def test_merge():
    # 0. Clean up
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    # 1. Load Data
    print("1. Loading lane-0.npy...")
    payload = {"raw_files": ["lane-0.npy"], "raw_data_dir": "TEMP1"}
    requests.post(f"{BASE_URL}/load", json=payload)
    
    # 2. Split lane-0 -> lane-0, lane-0_1
    print("2. Splitting lane-0...")
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
    print(f"   Files after split: {files}")
    if "lane-0_1.npy" not in files:
        print("FAILURE: lane-0_1.npy not found.")
        return

    # 3. Reload lane-0.npy (should auto-load lane-0_1.npy)
    print("3. Reloading lane-0.npy...")
    payload = {"raw_files": ["lane-0.npy"], "raw_data_dir": "TEMP1"}
    resp = requests.post(f"{BASE_URL}/load", json=payload)
    data = resp.json()
    file_names = data['file_names']
    print(f"   Loaded files: {file_names}")
    
    if "lane-0_1.npy" not in file_names:
        print("FAILURE: lane-0_1.npy not loaded.")
        return
        
    # 4. Connect lane-0 and lane-0_1
    print("4. Connecting lane-0 and lane-0_1...")
    nodes = data['nodes']
    # Find a node in zone 0 and a node in zone 1
    # Assuming lane-0 is index 0, lane-0_1 is index 1
    
    # Map filenames to indices
    idx0 = file_names.index("lane-0.npy")
    idx1 = file_names.index("lane-0_1.npy")
    
    node0 = None
    node1 = None
    
    for n in nodes:
        if int(n[4]) == idx0:
            node0 = n[0]
        elif int(n[4]) == idx1:
            node1 = n[0]
        
        if node0 is not None and node1 is not None:
            break
            
    if node0 is None or node1 is None:
        print("FAILURE: Could not find nodes in both zones.")
        return
        
    print(f"   Connecting node {node0} (zone {idx0}) and node {node1} (zone {idx1})")
    requests.post(f"{BASE_URL}/operation", json={
        "operation": "add_edge",
        "params": {"from_id": node0, "to_id": node1}
    })
    
    # 5. Unload lane-0.npy (should trigger merge)
    print("5. Unloading lane-0.npy...")
    requests.post(f"{BASE_URL}/unload", json={"filename": "lane-0.npy"})
    
    # 6. Check files
    files = os.listdir(TEMP_DIR)
    print(f"   Files after merge: {files}")
    
    if "lane-0_1.npy" in files:
        print("FAILURE: lane-0_1.npy was NOT deleted.")
    else:
        print("SUCCESS: lane-0_1.npy was deleted.")
        
    # Verify lane-0.npy size
    lane0_path = os.path.join(TEMP_DIR, "lane-0.npy")
    if os.path.exists(lane0_path):
        pts = np.load(lane0_path)
        print(f"   lane-0.npy has {len(pts)} points.")

if __name__ == "__main__":
    test_merge()
