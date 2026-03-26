import json
import os

def set_all_nodes_properties(file_path):
    """
    Sets 'yaw', 'zone', 'width', and 'indicator' to 0 for every node in the given JSON file.
    Preserves 'x', 'y', and 'id'.
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    try:
        print(f"Loading {file_path}...")
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'nodes' in data and isinstance(data['nodes'], list):
            node_count = len(data['nodes'])
            print(f"Updating properties for {node_count} nodes...")
            
            for node in data['nodes']:
                # Set specific properties to 0.0
                # node['yaw'] = 0.0
                node['zone'] = 0.0
                node['width'] = 0.0
                node['indicator'] = 0.0
                
                # Verify that x, y, id are present (optional check, but good for safety)
                if 'x' not in node or 'y' not in node or 'id' not in node:
                    print(f"Warning: Node missing essential fields: {node}")
            
            print(f"Saving changes back to {file_path}...")
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Successfully updated all {node_count} nodes.")
        else:
            print("Error: No 'nodes' list found in the JSON file.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    target_file = r"F:\RunningProjects\LaneMappingTool\web\backend\workspace\output.json"
    set_all_nodes_properties(target_file)
