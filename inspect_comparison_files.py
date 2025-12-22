import numpy as np
import pickle
import os

files = [
    r"f:/RunningProjects/LaneMappingTool/lanes/Gitam_lanes/Gitam.npy",
    r"f:/RunningProjects/LaneMappingTool/web/backend/workspace/output.pickle",
    r"G:/RunningProjects/Buggy/vechicalFileByInfCmp/sb_main_gate.pickel"
]

for f in files:
    print(f"--- Inspecting {f} ---")
    if not os.path.exists(f):
        print("File not found")
        continue
    
    try:
        if f.endswith('.npy'):
            data = np.load(f)
            print("Type:", type(data))
            print("Shape:", data.shape)
            if data.size > 0:
                print("Dtype:", data.dtype)
                print("First row:", data[0])
        elif f.endswith('.pickle') or f.endswith('.pickel'):
            try:
                with open(f, 'rb') as pf:
                    data = pickle.load(pf)
            except UnicodeDecodeError:
                print("Retry with latin1 encoding...")
                with open(f, 'rb') as pf:
                    data = pickle.load(pf, encoding='latin1')
            
            print("Type:", type(data))
            if isinstance(data, dict):
                print("Keys:", data.keys())
                for k in list(data.keys())[:3]:
                    print(f"Key {k} type:", type(data[k]))
                    # Check for steering clues
                    if 'steering' in k.lower() or 'angle' in k.lower():
                        print(f"Potential steering key: {k}")
            elif isinstance(data, list):
                print("Length:", len(data))
                if len(data) > 0:
                    print("First item type:", type(data[0]))
                    print("First item:", data[0])
            elif hasattr(data, 'nodes') and hasattr(data, 'edges'): # NetworkX graph
                print("Graph nodes:", len(data.nodes))
                print("Graph edges:", len(data.edges))
            else:
                print("Data:", data)
    except Exception as e:
        print("Error:", e)
    print("\n")
