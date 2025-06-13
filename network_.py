import argparse
import math
import os

import networkx as nx

import network_view2

# from networkx.readwrite import gpickle
print(nx.__file__)
print(nx.__version__)

import numpy as np

threshold_distance = 10
threshold_degree = 0.7


def transform_to_reference(x, y, yaw, reference_yaw):
    angle_diff = reference_yaw - yaw
    x_transformed = x * math.cos(angle_diff) - y * math.sin(angle_diff)
    y_transformed = x * math.sin(angle_diff) + y * math.cos(angle_diff)
    return x_transformed, y_transformed


def determine_front_and_back(x1, y1, yaw1, x2, y2, yaw2):
    reference_yaw = 0  # Choose a reference direction, in this case, 0 degrees

    # Transform points to the reference angle
    x1_transformed, y1_transformed = transform_to_reference(x1, y1, yaw1, reference_yaw)
    x2_transformed, y2_transformed = transform_to_reference(x2, y2, yaw2, reference_yaw)

    distance1 = math.sqrt(x1_transformed ** 2 + y1_transformed ** 2)
    distance2 = math.sqrt(x2_transformed ** 2 + y2_transformed ** 2)

    # Determine which point is farther from the origin
    if distance1 >= distance2:
        # if x1_transformed >= x2_transformed :
        return True
    else:
        return False


def add_node(G1, traj_data1, first_node_index):
    global threshold_distance, threshold_degree
    # Add nodes to the graph from trajectory 1 data
    for i in range(len(traj_data1)):
        x, y, yaw, = traj_data1[i]
        t = first_node_index + i
        G1.add_node(t, x=x, y=y, yaw=yaw, zone=0, width=0, indicator=0)
    last_node_index = i
    # Add edges to the graph for trajectory 1
    for i in range(len(traj_data1) - 1):
        t = first_node_index + i
        G1.add_edge(t, t + 1, weight=math.sqrt(
            (traj_data1[i + 1][0] - traj_data1[i][0]) ** 2 + (traj_data1[i + 1][1] - traj_data1[i][1]) ** 2))

    # Adjust this range based on your specific subset
    subset_nodes = range(first_node_index, last_node_index + 1)

    # # Find leaf nodes within a subset of nodes (between start_node and end_node)
    # leaf_nodes = [node for node in subset_nodes if len(G1.successors(node)) == 0]
    #
    # # Find nodes without predecessors (sink nodes)
    # sink_nodes = [node for node in subset_nodes if len(G1.predecessors(node)) == 0]

    leaf_nodes = [node for node in subset_nodes if len(list(G1.successors(node))) == 0]
    sink_nodes = [node for node in subset_nodes if len(list(G1.predecessors(node))) == 0]

    isolated_nodes = list(set(leaf_nodes + sink_nodes))
    for i in range(len(isolated_nodes)):
        for j in range(i + 1, len(isolated_nodes)):
            node1 = isolated_nodes[i]
            node2 = isolated_nodes[j]
            data1 = G1.nodes[node1]
            data2 = G1.nodes[node2]

            distance = math.sqrt((data1['x'] - data2['x']) ** 2 + (data1['y'] - data2['y']) ** 2)
            angle_diff = abs(((data1['yaw'] - data2['yaw']) + math.pi) % (2 * math.pi) - math.pi)

            if threshold_distance < 0.5 and angle_diff < threshold_degree:
                print("Nodes", node1, "and", node2, "meet the conditions.")
                # if(determine_front_and_back(data1['x'] ,data1['y'],data1['yaw'],data2['x'] ,data2['y'],data2['yaw'])):
                G1.add_edge(node2, node1, weight=distance)
                # else:    
                G1.add_edge(node1, node2, weight=distance)

    # Merge nodes based on Euclidean distance
    if (first_node_index != 0):
        for node1, data1 in G1.nodes(data=True):
            for node2, data2 in G1.nodes(data=True):
                if node1 < first_node_index and node2 >= first_node_index:
                    distance = math.sqrt((data1['x'] - data2['x']) ** 2 + (data1['y'] - data2['y']) ** 2)
                    if distance < threshold_distance and abs(
                            (((data1['yaw'] - data2['yaw']) + 3.14159) % 6.28319) - 3.14159) < threshold_degree:
                        # if(determine_front_and_back(data1['x'] ,data1['y'],data1['yaw'],data2['x'] ,data2['y'],data2['yaw'])):
                        G1.add_edge(node2, node1, weight=distance)
                        # else:    
                        G1.add_edge(node1, node2, weight=distance)
    return G1


def main(args):
    global threshold_distance, threshold_degree

    # Create an empty directed graph for trajectory 1
    G1 = nx.DiGraph()
    total = 0
    for lane_file in args.lane_files:
        if not os.path.exists(lane_file):
            print('File ', lane_file, ' not found. Skipping...')
            continue
        traj_data1 = np.load(lane_file)
        print(traj_data1)
        if (G1.nodes()):
            first_node_index = max(G1.nodes()) + 1
            total = first_node_index;
            print("first_node_index :", first_node_index)
        else:
            first_node_index = total

        G1 = add_node(G1, traj_data1, first_node_index)
    nx.write_gpickle(G1, args.output_file)
    # gpickle.write_gpickle(G1, args.output_file)


parser = argparse.ArgumentParser(description="Process lane.npy files and build a directional graph.")
parser.add_argument("lane_files", nargs="*", default=["WorkingLane.npy"],
                    help="List of lane.npy file locations (default: WorkingLane.npy)"
                    )

# Optional named argument
parser.add_argument("-o", "--output_file", default="output.pickle",
                    help="Output pickle file to save the graph (default: output.pickle)"
                    )
args = parser.parse_args()


def pickerGenerateViewer():
    global args
    main(args)
    network_view2.main()


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Process lane.npy files and build a directional graph.")
    # parser.add_argument("lane_files", nargs="*", default=["WorkingLane.npy"],
    #                     help="List of lane.npy file locations (default: WorkingLane.npy)"
    #                     )
    #
    # # Optional named argument
    # parser.add_argument("-o", "--output_file", default="output.pickle",
    #                     help="Output pickle file to save the graph (default: output.pickle)"
    #                     )
    # args = parser.parse_args()
    main(args)
    network_view2.main()
