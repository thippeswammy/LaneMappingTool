
import pickle
import networkx as nx
import numpy as np

G = nx.DiGraph()
# Add meaningful node data matching bp.py requirements
G.add_node(1, x=10.0, y=10.0, yaw=0.0, zone=0.0, width=3.0, indicator=0.0)
G.add_node(2, x=20.0, y=10.0, yaw=0.0, zone=0.0, width=3.0, indicator=0.0)
G.add_edge(1, 2, weight=10.0)

with open("vehicle_test_data.pickle", "wb") as f:
    pickle.dump(G, f, protocol=2)
