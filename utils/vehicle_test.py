#!/usr/bin/env python
import math
import pickle
import sys

import networkx as nx
import numpy as np

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: Matplotlib not found. Visualization will be disabled.")

# Try importing scipy for KDTree (mimicking bp.py)
try:
    from scipy.spatial import KDTree

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Warning: Scipy not found. KDTree tests will be skipped.")


def check_graph_loading(pickle_path):
    print("\n--- Test 1: Loading Graph ---")
    try:
        # Try NetworkX 1.x / 2.x method (Vehicle)
        if hasattr(nx, 'read_gpickle'):
            G = nx.read_gpickle(pickle_path)
        else:
            # Fallback for NetworkX 3.x (Local Test)
            with open(pickle_path, 'rb') as f:
                G = pickle.load(f)

        print("Success: Graph loaded.")
        print("Nodes: {}, Edges: {}".format(len(G.nodes()), len(G.edges())))
        return G
    except Exception as e:
        print("Failure: Could not load graph.")
        print("Error: {}".format(e))
        return None


def check_attributes(G):
    print("\n--- Test 2: Node Attributes ---")
    if len(G.nodes()) == 0:
        print("Skipping: Graph is empty.")
        return

    # Check first node
    nodes_list = list(G.nodes())
    node_id = nodes_list[0]

    try:
        data = G.nodes[node_id]  # NetworkX 2.x/3.x
    except (AttributeError, TypeError):
        data = G.node[node_id]  # NetworkX 1.x (bp.py/legacy)

    print("Sample Node ID: {} (Type: {})".format(node_id, type(node_id)))
    print("Attributes: {}".format(data.keys()))

    required_attrs = ['x', 'y', 'yaw', 'zone', 'width', 'indicator']
    missing = [attr for attr in required_attrs if attr not in data]

    if missing:
        print("Failure: Missing attributes: {}".format(missing))
    else:
        print("Success: All required attributes present.")

    # Check types of x, y
    if isinstance(data['x'], (float, int)) and not isinstance(data['x'], np.generic):
        print("Success: Attribute 'x' is native Python type.")
    else:
        print("Warning: Attribute 'x' might be Numpy type: {}".format(type(data['x'])))


def test_closest_node_task1(G):
    print("\n--- Test 3: Closest Node (Task1 Logic) ---")
    # Mimic task1.py logic
    # Find closest node to internal point 0
    if len(G.nodes()) == 0: return

    target_id = list(G.nodes())[0]
    try:
        target_data = G.nodes[target_id]
    except:
        target_data = G.node[target_id]
    tx, ty, tyaw = target_data['x'] + 0.5, target_data['y'] + 0.5, target_data['yaw']

    print("Searching for node closest to: ({}, {})".format(tx, ty))

    distances = []
    for node in G.nodes():
        try:
            data = G.nodes[node]
        except:
            data = G.node[node]
        dist = math.sqrt((data['x'] - tx) ** 2 + (data['y'] - ty) ** 2)
        # partial yaw check simulation
        if abs(data['yaw'] - tyaw) < 0.5:
            distances.append((node, dist))

    if not distances:
        print("Failure: No nodes found near target.")
    else:
        closest = min(distances, key=lambda x: x[1])
        print("Success: Found closest node {} at dist {}".format(closest[0], closest[1]))
        if closest[0] == target_id:
            print("Perfect match with expected node or neighbor.")


def test_kdtree_bp(G):
    print("\n--- Test 4: KDTree Creation (BP Logic) ---")
    if not HAS_SCIPY:
        print("Skipped (No Scipy)")
        return

    waypoints = []
    # Extract x,y for KDTree
    for node in G.nodes():
        try:
            data = G.nodes[node]
        except:
            data = G.node[node]
        waypoints.append([data['x'], data['y']])

    try:
        tree = KDTree(waypoints)
        print("Success: KDTree created with {} points.".format(len(waypoints)))

        # Test query
        dist, ind = tree.query([waypoints[0][0], waypoints[0][1]], k=1)
        print("Tree Query Test: Dist={}, Index={}".format(dist, ind))
    except Exception as e:
        print("Failure: KDTree operations failed.")
        print("Error: {}".format(e))


def test_shortest_path(G):
    print("\n--- Test 5: Shortest Path ---")
    nodes = list(G.nodes())
    if len(nodes) < 2:
        print("Skipping: Not enough nodes.")
        return

    source = nodes[0]
    target = nodes[min(5, len(nodes) - 1)]  # Try a nearby node

    try:
        if nx.has_path(G, source, target):
            path = nx.shortest_path(G, source, target, weight='weight')
            print("Success: Path found from {} to {} (Length: {})".format(source, target, len(path)))
        else:
            print("Notice: No path between {} and {} (Might be expected)".format(source, target))
    except Exception as e:
        print("Failure: Shortest path calculation crashed.")
        print("Error: {}".format(e))

def interactive_path_test(G):
    print("\n--- Test 6: Interactive Plotting ---")
    if not HAS_MATPLOTLIB:
        print("Skipping: Matplotlib not available.")
        return

    print("Launching interactive graph view...")
    print("INSTRUCTIONS: 1. Click 'Start' point. 2. Click 'End' point. (Check plot window)")

    # Extract coordinates
    node_coords = {}
    x_vals = []
    y_vals = []
    
    for node in G.nodes():
        try:
            data = G.nodes[node]
        except:
            data = G.node[node]
        node_coords[node] = (data['x'], data['y'])
        x_vals.append(data['x'])
        y_vals.append(data['y'])

    # Plot Graph
    plt.figure("Vehicle Graph Verification")
    plt.axis('equal')
    plt.grid(True)
    
    # Plot edges
    for u, v in G.edges():
        if u in node_coords and v in node_coords:
            ux, uy = node_coords[u]
            vx, vy = node_coords[v]
            plt.plot([ux, vx], [uy, vy], 'gray', markersize=0, linewidth=1, alpha=0.5)

    # Plot nodes
    plt.scatter(x_vals, y_vals, c='blue', s=10, label='Nodes')
    plt.title("Click START and END points")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.legend()
    
    # Wait for clicks
    try:
        pts = plt.ginput(2, timeout=0)
        if len(pts) < 2:
            print("Selection cancelled.")
            plt.close()
            return
            
        start_pt = pts[0]
        end_pt = pts[1]
        print("Clicked Start: ({:.2f}, {:.2f})".format(start_pt[0], start_pt[1]))
        print("Clicked End:   ({:.2f}, {:.2f})".format(end_pt[0], end_pt[1]))
        
        # Find closest nodes (reusing the logic from mimic function)
        def find_closest(tx, ty):
            best_node = None
            best_dist = float('inf')
            for node, (nx, ny) in node_coords.items():
                dist = math.sqrt((nx - tx)**2 + (ny - ty)**2)
                if dist < best_dist:
                    best_dist = dist
                    best_node = node
            return best_node, best_dist

        start_node, s_dist = find_closest(start_pt[0], start_pt[1])
        end_node, e_dist = find_closest(end_pt[0], end_pt[1])
        
        print("Mapped Start -> Node {} (Dist: {:.2f}m)".format(start_node, s_dist))
        print("Mapped End   -> Node {} (Dist: {:.2f}m)".format(end_node, e_dist))
        
        # Plot selection
        plt.plot(start_pt[0], start_pt[1], 'go', markersize=10, label='Click Start')
        plt.plot(end_pt[0], end_pt[1], 'ro', markersize=10, label='Click End')
        
        # Calculate Path
        if nx.has_path(G, start_node, end_node):
            path = nx.shortest_path(G, start_node, end_node, weight='weight')
            print("Shortest path found! Length: {} steps".format(len(path)))
            
            # Visualize Path
            path_x = []
            path_y = []
            for n in path:
                path_x.append(node_coords[n][0])
                path_y.append(node_coords[n][1])
            
            plt.plot(path_x, path_y, 'r-', linewidth=2, label='Path')
            plt.title("Path Found: {} -> {}".format(start_node, end_node))
        else:
            print("No path found between selected nodes.")
            plt.title("No Path Found!")
            
        plt.legend()
        plt.show()
        
    except Exception as e:
        print("Interaction error: {}".format(e))


if __name__ == "__main__":
    pickle_file = "output.pickle"
    if len(sys.argv) > 1:
        pickle_file = sys.argv[1]

    print("Running Vehicle Compatibility Test Suite")
    print("Target File: {}".format(pickle_file))

    G = check_graph_loading(pickle_file)
    if G:
        check_attributes(G)
        test_closest_node_task1(G)
        test_kdtree_bp(G)
        test_shortest_path(G)
        
        if "--no-plot" not in sys.argv:
            interactive_path_test(G)
        else:
            print("\nSkipping interactive plot (--no-plot specified)")
