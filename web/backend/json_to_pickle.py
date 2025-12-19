#!/usr/bin/env python
import json
import os
import sys

import networkx as nx
from networkx.readwrite import json_graph


def convert_json_to_pickle(json_path, pickle_path):
    """
    Reads a NetworkX graph from a JSON file (node-link format) and saves it as a Pickle.
    Compatible with Python 2.7 and older NetworkX versions.
    """
    if not os.path.exists(json_path):
        print("Error: JSON file '{}' not found.".format(json_path))
        sys.exit(1)

    print("Loading JSON from '{}'...".format(json_path))
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print("Error reading JSON file: {}".format(e))
        sys.exit(1)

    print("Converting to NetworkX graph...")
    try:
        # node_link_graph handles the reconstruction of the graph object
        G = json_graph.node_link_graph(data)
        
        # JSON keys are always strings, but our original graph used integers.
        # We must convert node IDs back to int to match legacy behavior.
        print("Converting node IDs to integers...")
        G = nx.relabel_nodes(G, int)
        
    except Exception as e:
        print("Error converting JSON to Graph: {}".format(e))
        sys.exit(1)

    print("Graph Info: Nodes: {}, Edges: {}".format(len(G.nodes()), len(G.edges())))

    print("Saving to Pickle '{}'...".format(pickle_path))
    try:
        nx.write_gpickle(G, pickle_path)
        print("Success! Pickle file created.")
    except Exception as e:
        print("Error writing pickle file: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    # Default paths
    input_json = "output.json"
    output_pickle = "output.pickle"

    # Simple argument parsing
    if len(sys.argv) > 1:
        input_json = sys.argv[1]
    if len(sys.argv) > 2:
        output_pickle = sys.argv[2]

    print("--------------------------------------------------")
    print("JSON to Pickle Converter (Python 2 Compatible)")
    print("--------------------------------------------------")
    convert_json_to_pickle(input_json, output_pickle)
