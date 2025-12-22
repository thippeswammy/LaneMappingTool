import pickle
import networkx as nx

f = r"G:/RunningProjects/Buggy/vechicalFileByInfCmp/sb_main_gate.pickel"

try:
    with open(f, 'rb') as pf:
        G = pickle.load(pf, encoding='latin1')
except Exception as e:
    print(f"Load failed: {e}")
    G = None

if G:
    print(f"Type: {type(G)}")
    print(f"Dir: {dir(G)}")
    try:
        print(f"Dict keys: {G.__dict__.keys()}")
        if '_node' in G.__dict__:
            print(f"Type of _node: {type(G.__dict__['_node'])}")
            print(f"Dir of _node: {dir(G.__dict__['_node'])}")
    except Exception as e:
        print(f"Dict inspection failed: {e}")
