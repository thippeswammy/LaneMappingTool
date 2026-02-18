import json
import networkx as nx
from collections import deque

def resequence_nodes(file_path, start_node_id):
    try:
        print(f"Loading {file_path}...")
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        nodes = data.get('nodes', [])
        links = data.get('links', [])
        
        # Build mapping from old ID to node object for quick access
        node_map = {node['id']: node for node in nodes}
        
        if start_node_id not in node_map:
            print(f"Error: Start node ID {start_node_id} not found.")
            return

        # build adjacency list for traversal 
        # (using a simple dict for adjacency to control traversal order if needed, or networkx)
        # Using NetworkX ensures we handle connectivity easily
        G = nx.DiGraph()
        for link in links:
            G.add_edge(link['source'], link['target'])
            
        # BFS Traversal to determine new order
        # We want a deterministic order, so we'll use a standard queue-based BFS
        # and sort neighbors to ensure reproducibility if multiple exist
        
        visited = set()
        queue = deque([start_node_id])
        visited.add(start_node_id)
        
        new_id_map = {} # old_id -> new_id
        current_new_id = 0
        
        order = []
        
        print("Starting BFS traversal...")
        while queue:
            current_node = queue.popleft()
            
            # mental check: is this node in our node list? (it should be if links are valid)
            if current_node in node_map:
                order.append(current_node)
                new_id_map[current_node] = current_new_id
                current_new_id += 1
            
            # Get neighbors
            if current_node in G:
                neighbors = sorted(list(G.successors(current_node)))
                for neighbor in neighbors:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                        
        print(f"Traversal complete. Reached {len(order)} nodes.")
        
        if len(order) < len(nodes):
            print(f"Warning: {len(nodes) - len(order)} nodes were not reachable and will be appended with subsequent IDs.")
            # Append remaining nodes in their original order (or sorted by old ID)
            remaining_nodes = sorted([n['id'] for n in nodes if n['id'] not in visited])
            for old_id in remaining_nodes:
                 order.append(old_id)
                 new_id_map[old_id] = current_new_id
                 current_new_id += 1
        
        # Construct new nodes list
        new_nodes = []
        for old_id in order:
            original_node = node_map[old_id].copy()
            original_node['id'] = new_id_map[old_id]
            # Ensure other properties are zeroed as per previous requirements if they weren't already?
            # actually, let's just keep them as is (which are likely 0 from previous step)
            new_nodes.append(original_node)
            
        # Construct new links list
        new_links = []
        for link in links:
            source = link['source']
            target = link['target']
            
            # Only include links where both source and target exist in our new map
            # (which should be all of them if the graph was consistent)
            if source in new_id_map and target in new_id_map:
                new_link = link.copy()
                new_link['source'] = new_id_map[source]
                new_link['target'] = new_id_map[target]
                new_links.append(new_link)
            else:
                 print(f"Warning: Skipping link {source}->{target} due to missing node key.")
                 
        # Create new data structure
        new_data = data.copy()
        new_data['nodes'] = new_nodes
        new_data['links'] = new_links
        
        save_path = file_path # Overwrite or create new? Let's overwrite as implied by "work on output.json"
        
        print(f"Saving re-sequenced graph to {save_path}...")
        with open(save_path, 'w') as f:
            json.dump(new_data, f, indent=4)
            
        print("Done.")
        print(f"Node {start_node_id} is now ID {new_id_map[start_node_id]} (should be 0)")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    target_file = r"F:\RunningProjects\LaneMappingTool\web\backend\workspace\output.json"
    resequence_nodes(target_file, 2623)
