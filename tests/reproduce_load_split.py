import requests
import json
import os
import shutil
import numpy as np

BASE_URL = "http://127.0.0.1:5001/api"
TEMP_DIR = os.path.join("workspace", "temp_lanes")

def reproduce_load():
    # 0. Clean up
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    # 1. Load Data
    print("1. Loading lane-0.npy...")
    payload = {"raw_files": ["lane-0.npy"], "raw_data_dir": "Gitam_lanes"}
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

    # 3. Reload ONLY lane-0.npy
    print("3. Reloading ONLY lane-0.npy...")
    payload = {"raw_files": ["lane-0.npy"], "raw_data_dir": "Gitam_lanes"}
    resp = requests.post(f"{BASE_URL}/load", json=payload)
    
    data = resp.json()
    loaded_files = data['file_names']
    print(f"   Loaded files: {loaded_files}")
    
    if "lane-0_1.npy" in loaded_files:
        print("SUCCESS: lane-0_1.npy was automatically loaded.")
    else:
        print("FAILURE: lane-0_1.npy was NOT loaded.")

if __name__ == "__main__":
    reproduce_load()
