import math
import os
import pickle
import sys


def calculate_yaw(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1)


def fix_yaw(input_path, output_path):
    print(f"Loading graph from {input_path}...")
    try:
        with open(input_path, 'rb') as f:
            G = pickle.load(f)
    except Exception as e:
        print(f"Error loading pickle: {e}")
        return

    print(f"Graph loaded. Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

    updated_count = 0

    # Sort nodes to process sequentially if possible (heuristic)
    # This helps if we want to print progress, but graph logic doesn't depend on order.

    for node in G.nodes():
        # Get current node data
        # Handle different NetworkX versions (G.nodes[n] vs G.node[n])
        try:
            data = G.nodes[node]
        except TypeError:
            data = G.node[node]

        x = data['x']
        y = data['y']

        # Find successors (outgoing edges)
        successors = list(G.successors(node))

        new_yaw = None

        if successors:
            # Use the first successor (assuming simple lines usually)
            # If multiple (junction), using the first one is an approximation but better than random noise.
            # Ideally we'd average them or something, but standard logic is usually "towards next".
            next_node = successors[0]
            try:
                next_data = G.nodes[next_node]
            except TypeError:
                next_data = G.node[next_node]

            nx_coord = next_data['x']
            ny_coord = next_data['y']

            new_yaw = calculate_yaw(x, y, nx_coord, ny_coord)

        else:
            # No successor. Check predecessors (end of line).
            predecessors = list(G.predecessors(node))
            if predecessors:
                prev_node = predecessors[0]
                try:
                    prev_data = G.nodes[prev_node]
                except TypeError:
                    prev_data = G.node[prev_node]

                px_coord = prev_data['x']
                py_coord = prev_data['y']

                # Yaw is same as previous segment
                new_yaw = calculate_yaw(px_coord, py_coord, x, y)

        if new_yaw is not None:
            data['yaw'] = new_yaw
            updated_count += 1

    print(f"Recalculated yaw for {updated_count} nodes.")

    print(f"Saving fixed graph to {output_path}...")
    with open(output_path, 'wb') as f:
        pickle.dump(G, f, protocol=2)
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default paths
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web', 'backend', 'workspace'))
        default_input = os.path.join(base_dir, 'output.pickle')
        default_output = os.path.join(base_dir, 'output_fixed.pickle')

        if os.path.exists(default_input):
            print(f"No arguments provided. Using default: {default_input}")
            fix_yaw(default_input, default_output)
        else:
            print("Usage: python fix_pickle_yaw.py <input_pickle> [output_pickle]")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace(".pickle", "_fixed.pickle")
        fix_yaw(input_file, output_file)
