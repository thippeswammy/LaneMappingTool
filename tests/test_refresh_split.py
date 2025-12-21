import requests
import json
import os
import shutil
import numpy as np

BASE_URL = "http://127.0.0.1:5001/api"
TEMP_DIR = os.path.join("web", "backend", "workspace", "temp_lanes")

def test_refresh():
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

    # 3. Reset lane-0.npy (Refresh)
    print("3. Resetting lane-0.npy...")
    # Note: reset_temp_file expects raw_dir to find the original file
    payload = {"filename": "lane-0.npy", "raw_dir": "TEMP1"}
    requests.post(f"{BASE_URL}/reset_temp_file", json=payload)
    
    # Check files
    files = os.listdir(TEMP_DIR)
    print(f"   Files after reset: {files}")
    
    if "lane-0_1.npy" in files:
        print("FAILURE: lane-0_1.npy was NOT deleted.")
    else:
        print("SUCCESS: lane-0_1.npy was deleted.")

if __name__ == "__main__":
    test_refresh()
