import pickle
import networkx as nx
import os

def check_path():
    try:
        pickle_path = os.path.join("point_save", "output.pickle")
        with open(pickle_path, 'rb') as f:
            G = pickle.load(f)
        
        print(f"Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        start_node = 2515
        end_node = 4699
        
        if start_node not in G:
            print(f"Start node {start_node} not found in graph")
            return
        if end_node not in G:
            print(f"End node {end_node} not found in graph")
            return
            
        print(f"Start node {start_node} exists. Out degree: {G.out_degree(start_node)}")
        print(f"End node {end_node} exists. In degree: {G.in_degree(end_node)}")
        
        has_path = nx.has_path(G, start_node, end_node)
        print(f"Direct path exists: {has_path}")
        
        if has_path:
            path = nx.shortest_path(G, start_node, end_node)
            print(f"Shortest path length: {len(path)}")
        else:
            print("Trying undirected path...")
            has_undirected = nx.has_path(G.to_undirected(), start_node, end_node)
            print(f"Undirected path exists: {has_undirected}")
            
            # Check weakly connected components
            start_comp = None
            end_comp = None
            for i, comp in enumerate(nx.weakly_connected_components(G)):
                if start_node in comp:
                    start_comp = i
                if end_node in comp:
                    end_comp = i
            
            print(f"Start node component ID: {start_comp}")
            print(f"End node component ID: {end_comp}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_path()
