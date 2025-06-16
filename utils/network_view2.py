import pickle

import matplotlib.pyplot as plt
import networkx as nx

graph_file_path = r"./files\output.pickle"


def network_view2():
    # Load graph
    with open(graph_file_path, "rb") as f:
        data = pickle.load(f, encoding='latin1')

    # Extract graph
    if isinstance(data, (nx.Graph, nx.DiGraph)):
        G1 = data
    elif isinstance(data, dict):
        for k in data:
            if isinstance(data[k], (nx.Graph, nx.DiGraph)):
                G1 = data[k]
                print(f"Graph extracted from key: {k}")
                break
        else:
            raise ValueError("No NetworkX graph found in pickle data.")
    else:
        raise ValueError("Pickle file does not contain a NetworkX graph.")

    print(G1)

    # Extract positions or use fallback
    try:
        pos = {i: (attr['x'], attr['y']) for i, attr in G1.nodes(data=True)}
    except KeyError:
        print("No 'x' and 'y' attributes, using spring_layout.")
        pos = nx.spring_layout(G1)

    # ✅ Fix for matplotlib >=3.8: Create figure before drawing
    fig, ax = plt.subplots(figsize=(12, 8))
    nx.draw(G1, pos, with_labels=True, node_size=50, font_size=8, ax=ax)
    plt.title("Visualized Graph")
    plt.show()


if __name__ == "__main__":
    network_view2()
