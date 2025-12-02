import os
import sys
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS

# Adjust path to import from the parent project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.data_loader import DataLoader
from utils.data_manager import DataManager
from web.backend.utils.curve_utils import find_path, smooth_segment

# --- App Setup ---
app = Flask(__name__)
CORS(app)

# --- Data Loading ---
base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir, '../..'))

# Data is expected to be in lanes/TEMP1 relative to project root
# Default paths as requested
graph_dir = os.path.join(project_root, 'files')
lanes_root = os.path.join(project_root, 'lanes')
raw_data_path = os.path.join(lanes_root, 'TEMP1')

# Paths for saved working state
nodes_path = os.path.join(graph_dir, 'graph_nodes1.npy')
edges_path = os.path.join(graph_dir, 'graph_edges1.npy')

# These files must exist in your 'original_data_path' folder
files_path_ = [] # No default files
files_path = []

# Initialize DataLoader with default path
loader = DataLoader(raw_data_path)

# Initialize empty if not loading saved data
final_nodes = np.array([])
final_edges = np.array([])
file_names = []
D = 1.0

if os.path.exists(nodes_path) and os.path.exists(edges_path):
    final_nodes, final_edges, file_names, D = loader.load_graph_data(nodes_path, edges_path)

if final_nodes.size == 0:
    print("No data loaded at all.")
    final_nodes = np.array([])
    final_edges = np.array([])

data_manager = DataManager(final_nodes, final_edges, file_names)


# --- API Endpoints ---
@app.route('/api/data', methods=['GET'])
def get_data():
    nodes_list = data_manager.nodes.tolist() if data_manager.nodes.size > 0 else []
    edges_list = data_manager.edges.tolist() if data_manager.edges.size > 0 else []
    return jsonify({
        'nodes': nodes_list,
        'edges': edges_list,
        'file_names': data_manager.file_names
    })


@app.route('/api/save', methods=['POST'])
def save_data():
    """Saves the nodes and edges data from a POST request."""
    try:
        data = request.get_json()
        nodes_array = np.array(data['nodes'])
        edges_array = np.array(data['edges'])
        data_manager.nodes = nodes_array
        data_manager.edges = edges_array

        data_manager.save_by_web(graph_dir)

        return jsonify({'status': 'success', 'message': 'Data saved successfully.'})
    except Exception as e:
        print(f"Error saving data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/files', methods=['GET'])
def get_files():
    """List available raw data files and saved graph files.
    
    This function retrieves and lists the raw data files from a specified
    subdirectory and the saved graph files from another directory. It handles both
    absolute and relative paths for the subdirectories, defaults to predefined
    directories when necessary, and checks for the existence of these paths before
    attempting to list their contents. The results are returned in a JSON format,
    including the paths and available subdirectories.
    
    Returns:
        flask.Response: A JSON response containing lists of raw files, saved files, and relevant
            directory information.
    """
    try:
        # Get requested subdirectory for raw files, default to TEMP1
        subdir = request.args.get('subdir', 'TEMP1')
        
        if os.path.isabs(subdir):
            current_raw_path = subdir
        else:
            current_raw_path = os.path.join(lanes_root, subdir)
        
        # Get requested subdirectory for saved files, default to graph_dir
        saved_subdir = request.args.get('saved_subdir')
        if saved_subdir:
            if os.path.isabs(saved_subdir):
                current_saved_path = saved_subdir
            else:
                current_saved_path = os.path.join(graph_dir, saved_subdir)
        else:
            current_saved_path = graph_dir

        # List raw data files in the requested subdirectory
        raw_files = []
        if os.path.exists(current_raw_path):
            raw_files = [f for f in os.listdir(current_raw_path) if f.endswith('.npy')]

        # List available subdirectories in 'lanes'
        subdirs = []
        if os.path.exists(lanes_root):
            subdirs = [d for d in os.listdir(lanes_root) if os.path.isdir(os.path.join(lanes_root, d))]

        # List saved graph files
        saved_files = []
        if os.path.exists(current_saved_path):
            saved_files = [f for f in os.listdir(current_saved_path) if f.endswith('.npy')]

        return jsonify({
            'raw_files': raw_files,
            'saved_files': saved_files,
            'raw_path': current_raw_path,
            'saved_path': current_saved_path,
            'subdirs': subdirs,
            'current_subdir': subdir,
            'current_saved_subdir': saved_subdir
        })
    except Exception as e:
        print(f"Error listing files: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/load', methods=['POST'])
def load_data_endpoint():
    """Load selected raw files and/or saved graph files."""
    global data_manager, loader
    try:
        data = request.get_json()
        raw_files = data.get('raw_files', [])
        saved_nodes_file = data.get('saved_nodes_file')
        saved_edges_file = data.get('saved_edges_file')
        raw_data_dir = data.get('raw_data_dir')
        saved_graph_dir = data.get('saved_graph_dir') # New parameter

        print(f"Loading data: raw={raw_files}, nodes={saved_nodes_file}, edges={saved_edges_file}, dir={raw_data_dir}, saved_dir={saved_graph_dir}")

        # Update loader if a directory is specified
        if raw_data_dir:
             if os.path.isabs(raw_data_dir):
                 new_path = raw_data_dir
             else:
                 new_path = os.path.join(lanes_root, raw_data_dir)
                 
             if os.path.exists(new_path):
                 loader = DataLoader(new_path)
                 print(f"Updated loader path to: {new_path}")
             else:
                 print(f"Warning: Requested directory {new_path} does not exist. Using default.")

        # Initialize with current data if NOT loading a saved graph
        if saved_nodes_file and saved_edges_file:
            # We are loading a saved graph, so we start fresh
            final_nodes = np.array([])
            final_edges = np.array([])
            file_names = []
            D = 1.0
            
            # Determine path for saved files
            if saved_graph_dir:
                if os.path.isabs(saved_graph_dir):
                    load_path = saved_graph_dir
                else:
                    load_path = os.path.join(graph_dir, saved_graph_dir)
            else:
                load_path = graph_dir

            nodes_path_full = os.path.join(load_path, saved_nodes_file)
            edges_path_full = os.path.join(load_path, saved_edges_file)
            
            if os.path.exists(nodes_path_full) and os.path.exists(edges_path_full):
                g_nodes, g_edges, g_names, g_D = loader.load_graph_data(nodes_path_full, edges_path_full)
                
                if g_nodes.size > 0:
                    if final_nodes.size > 0:
                        # Calculate offsets
                        start_id_offset = int(np.max(final_nodes[:, 0])) + 1
                        lane_id_offset = int(np.max(final_nodes[:, 4])) + 1
                        
                        # Apply offsets to new graph data
                        g_nodes[:, 0] += start_id_offset
                        g_nodes[:, 4] += lane_id_offset
                        g_edges += start_id_offset
                        
                        # Update file names to reflect new lane IDs
                        unique_lanes = np.unique(g_nodes[:, 4]).astype(int)
                        g_names = [f"Edited Lane {i}" for i in unique_lanes]

                        # Merge
                        final_nodes = np.vstack([final_nodes, g_nodes])
                        final_edges = np.vstack([final_edges, g_edges])
                        file_names.extend(g_names)
                        D = max(D, g_D)
                    else:
                        final_nodes = g_nodes
                        final_edges = g_edges
                        file_names = g_names
                        D = g_D
                        
                print(f"Loaded and merged saved graph: {g_nodes.shape[0]} nodes")
            else:
                print("Saved graph files not found.")
        else:
            # We are NOT loading a saved graph, so preserve existing data
            final_nodes = data_manager.nodes.copy() if data_manager.nodes.size > 0 else np.array([])
            final_edges = data_manager.edges.copy() if data_manager.edges.size > 0 else np.array([])
            file_names = list(data_manager.file_names)
            D = loader.D # Best effort to keep D

        # 2. Load Raw Data if requested
        if raw_files:
            # Filter out already loaded files
            existing_files = set(data_manager.file_names)
            files_to_load = [f for f in raw_files if f not in existing_files]
            
            if not files_to_load:
                print("All selected files are already loaded.")
            else:
                print(f"Loading new files: {files_to_load}")
                # Calculate offsets
                start_id_offset = 0
                lane_id_offset = 0

                if final_nodes.size > 0:
                    start_id_offset = int(np.max(final_nodes[:, 0])) + 1
                    lane_id_offset = int(np.max(final_nodes[:, 4])) + 1

                new_nodes, new_edges, new_names = loader.load_data(
                    specific_files=files_to_load,
                    start_id=start_id_offset
                )

                if new_nodes.size > 0:
                    # Adjust Lane IDs
                    new_nodes[:, 4] += lane_id_offset

                    # Merge
                    if final_nodes.size > 0:
                        final_nodes = np.vstack([final_nodes, new_nodes])
                        final_edges = np.vstack([final_edges, new_edges])
                        file_names.extend(new_names)
                        D = max(D, loader.D)
                    else:
                        final_nodes = new_nodes
                        final_edges = new_edges
                        file_names = new_names
                        D = loader.D
                    
                    print(f"Merged raw files. Total: {final_nodes.shape[0]} nodes.")

        # Update DataManager
        if final_nodes.size == 0:
             # Initialize empty to avoid errors
            final_nodes = np.array([])
            final_edges = np.array([])
        
        data_manager = DataManager(final_nodes, final_edges, file_names)
        
        return jsonify({
            'status': 'success',
            'nodes': data_manager.nodes.tolist() if data_manager.nodes.size > 0 else [],
            'edges': data_manager.edges.tolist() if data_manager.edges.size > 0 else [],
            'file_names': data_manager.file_names
        })

    except Exception as e:
        print(f"Error loading data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/unload', methods=['POST'])
def unload_data_endpoint():
    """Handles the unloading of data files via a POST request.
    
    This function processes a request to unload a data file specified by  the
    'filename' key in the JSON payload. It checks for the presence of  the
    filename, attempts to remove the file using the data_manager, and  returns the
    current state of nodes, edges, and file names if successful.  In case of
    errors, appropriate error messages are returned.
    
    Returns:
        JSON response indicating the success or failure of the operation.
    """
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'status': 'error', 'message': 'No filename provided'}), 400

        success = data_manager.remove_file(filename)
        
        if success:
            return jsonify({
                'status': 'success',
                'nodes': data_manager.nodes.tolist(),
                'edges': data_manager.edges.tolist(),
                'file_names': [f for f in data_manager.file_names if f is not None]
            })
        else:
             return jsonify({'status': 'error', 'message': 'Failed to remove file'}), 500

    except Exception as e:
        print(f"Error unloading data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/smooth', methods=['POST'])
def smooth_path_endpoint():
    try:
        data = request.get_json()
        start_id = int(data.get('start_id'))
        end_id = int(data.get('end_id'))
        smoothness = float(data.get('smoothness', 1.0))
        weight = float(data.get('weight', 1.0))

        path_ids = find_path(data_manager.edges, start_id, end_id)
        if not path_ids:
            return jsonify({'status': 'error', 'message': 'No path found between nodes.'}), 404

        new_points_xy = smooth_segment(data_manager.nodes, data_manager.edges, path_ids, smoothness, weight)
        if new_points_xy is None:
            return jsonify({'status': 'error',
                            'message': 'Smoothing failed. Path may be too short, contain duplicates, or be invalid for B-Spline.'}), 400

        # Prepare the updated node data to be returned to the frontend
        updated_nodes_preview = []
        for i, point_id in enumerate(path_ids):
            node_mask = (data_manager.nodes[:, 0] == point_id)
            if np.any(node_mask):
                original_node = data_manager.nodes[node_mask][0]
                new_node = original_node.copy()
                new_node[1:3] = new_points_xy[i]

                # Calculate Yaw
                if i < len(new_points_xy) - 1:
                    dx = new_points_xy[i + 1, 0] - new_points_xy[i, 0]
                    dy = new_points_xy[i + 1, 1] - new_points_xy[i, 1]
                    new_node[3] = np.arctan2(dy, dx)
                elif i > 0:
                    # Last point inherits yaw from the previous one in the preview
                    new_node[3] = updated_nodes_preview[i - 1][3]

                updated_nodes_preview.append(new_node.tolist())

        return jsonify({
            'status': 'success',
            'updated_nodes': updated_nodes_preview
        })

    except Exception as e:
        print(f"Error during smoothing: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/operation', methods=['POST'])
def perform_operation():
    try:
        data = request.get_json()
        operation = data.get('operation')
        params = data.get('params')

        if operation == 'apply_updates':
            nodes_array = np.array(params['nodes'])
            edges_array = np.array(params['edges'])
            data_manager.nodes = nodes_array
            data_manager.edges = edges_array
            data_manager.history.append((data_manager.nodes.copy(), data_manager.edges.copy()))

        elif operation == 'add_node':
            x, y, lane_id = params['x'], params['y'], params['lane_id']
            new_node_id = data_manager.add_node(x, y, lane_id)
            print("add_node", params.get('from_id'), params.get('to_id'))
            if params.get('connect_to') is not None:
                data_manager.add_edge(params['connect_to'], new_node_id)

        elif operation == 'add_edge':
            print("add_edge", params['from_id'], params['to_id'])
            from_id, to_id = params['from_id'], params['to_id']
            data_manager.add_edge(from_id, to_id)

        elif operation == 'delete_points':
            point_ids = params['point_ids']
            data_manager.delete_points(point_ids)

        elif operation == 'copy_points':
            point_ids = params['point_ids']
            data_manager.copy_points(point_ids)

        elif operation == 'break_links':
            point_id = params['point_id']
            data_manager.delete_edges_for_node(point_id)

        elif operation == 'reverse_path':
            start_id, end_id = params['start_id'], params['end_id']
            path_ids = find_path(data_manager.edges, start_id, end_id)
            if path_ids:
                data_manager.reverse_path(path_ids)
            else:
                return jsonify({'status': 'error', 'message': 'No path found'}), 404

        elif operation == 'remove_between':
            start_id, end_id = params['start_id'], params['end_id']
            path_ids = find_path(data_manager.edges, start_id, end_id)
            if path_ids and len(path_ids) > 2:
                points_to_delete = path_ids[1:-1]
                data_manager.delete_points(points_to_delete)

        elif operation == 'undo':
            data_manager.undo()

        elif operation == 'redo':
            data_manager.redo()

        elif operation == 'batch_add_nodes':
            points = params.get('points', [])
            lane_id = params.get('lane_id', 0)
            connect_to_start_id = params.get('connect_to_start_id')

            previous_node_id = connect_to_start_id
            new_node_ids = []

            for point in points:
                x, y = point['x'], point['y']
                new_node_id = data_manager.add_node(x, y, lane_id)
                new_node_ids.append(new_node_id)

                if previous_node_id is not None:
                    data_manager.add_edge(previous_node_id, new_node_id)
                previous_node_id = new_node_id

        else:
            return jsonify({'status': 'error', 'message': f'Unknown operation: {operation}'}), 400

        return jsonify({
            'status': 'success',
            'nodes': data_manager.nodes.tolist(),
            'edges': data_manager.edges.tolist()
        })
    except Exception as e:
        print(f"Error performing operation '{operation}': {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
