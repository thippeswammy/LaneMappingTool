import pickle
import os

path = r"G:/RunningProjects/Buggy/vechicalFileByInfCmp/sb_main_gate.pickel"

try:
    with open(path, 'rb') as f:
        G = pickle.load(f)
except UnicodeDecodeError:
    with open(path, 'rb') as f:
        G = pickle.load(f, encoding='latin1')

print(f"Type of G: {type(G)}")
print("Inspecting G.__dict__ keys:")
try:
    for k, v in G.__dict__.items():
        print(f"  Key: {k}, Type: {type(v)}")
        if k in ['_node', 'node', '_adj', 'adj', 'graph']:
            try:
                print(f"    Value repr (short): {str(v)[:100]}")
                if isinstance(v, dict):
                    print(f"    Keys sample: {list(v.keys())[:5]}")
            except Exception as e:
                print(f"    Error printing value: {e}")
except Exception as e:
    print(f"Error accessing __dict__: {e}")
