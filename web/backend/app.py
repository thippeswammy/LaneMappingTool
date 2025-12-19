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
graph_dir = os.path.join(base_dir, "workspace")
lanes_root = os.path.join(project_root, 'lanes')
raw_data_path = os.path.join(lanes_root, 'TEMP1')
TEMP_LANES_DIR = os.path.join(graph_dir, "temp_lanes")

# Paths for saved working state
nodes_path = os.path.join(graph_dir, 'graph_nodes0.npy')
edges_path = os.path.join(graph_dir, 'graph_edges0.npy')

# These files must exist in your 'original_data_path' folder
files_path_ = []  # No default files
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
    try:
        data = request.get_json()
        nodes_array = np.array(data['nodes'])
        edges_array = np.array(data['edges'])
        data_manager.nodes = nodes_array
        data_manager.edges = edges_array
        data_manager.sync_next_id()

        data_manager.save_by_web(os.path.join(base_dir, "workspace"))
        
        # Save temp lanes
        split_map, merged_files = data_manager.save_temp_lanes(TEMP_LANES_DIR)
        
        if merged_files:
            print(f"Files merged away during save: {merged_files}")
            for mf in merged_files:
                fpath = os.path.join(TEMP_LANES_DIR, mf)
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                        print(f"Deleted merged-away file: {fpath}")
                    except Exception as e:
                        print(f"Error deleting merged file {fpath}: {e}")

        return jsonify({'status': 'success', 'message': 'Data saved successfully'})
    except Exception as e:
        print(f"Error saving data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/files', methods=['GET'])
def get_files():
    """List available raw data files and saved graph files."""
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


import shutil

# ... (imports)

# ... (existing code)

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
        saved_graph_dir = data.get('saved_graph_dir')  # New parameter

        print(
            f"Loading data: raw={raw_files}, nodes={saved_nodes_file}, edges={saved_edges_file}, dir={raw_data_dir}, saved_dir={saved_graph_dir}")

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
            # ... (saved graph loading logic remains same)
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
            D = loader.D  # Best effort to keep D

        # 2. Load Raw Data if requested
        if raw_files:
            # Filter out already loaded files
            existing_files = set(data_manager.file_names)
            files_to_load = [f for f in raw_files if f not in existing_files]

            if not files_to_load:
                print("All selected files are already loaded.")
            else:
                print(f"Loading new files: {files_to_load}")
                
                # Expand files_to_load to include split parts from TEMP_LANES_DIR
                expanded_files_to_load = []
                for filename in files_to_load:
                    expanded_files_to_load.append(filename)
                    
                    # Check for split parts
                    if os.path.exists(TEMP_LANES_DIR):
                        base_name, ext = os.path.splitext(filename)
                        prefix = f"{base_name}_"
                        
                        for f in os.listdir(TEMP_LANES_DIR):
                            if f.startswith(prefix) and f.endswith(ext):
                                # Avoid duplicates if already in request (unlikely but safe)
                                if f not in expanded_files_to_load and f not in existing_files:
                                    expanded_files_to_load.append(f)
                                    print(f"Auto-loading split part: {f}")
                
                files_to_load = expanded_files_to_load
                
                # Calculate offsets
                start_id_offset = 0
                lane_id_offset = 0

                if final_nodes.size > 0:
                    start_id_offset = int(np.max(final_nodes[:, 0])) + 1
                    lane_id_offset = len(file_names)
                else:
                    start_id_offset = 0
                    lane_id_offset = 0

                # Ensure TEMP_LANES_DIR exists
                if not os.path.exists(TEMP_LANES_DIR):
                    os.makedirs(TEMP_LANES_DIR)

                loaded_nodes_list = []
                loaded_edges_list = []
                loaded_names_list = []
                
                current_pid = start_id_offset
                
                for i, filename in enumerate(files_to_load):
                    temp_path = os.path.join(TEMP_LANES_DIR, filename)
                    raw_path = os.path.join(loader.directory, filename)
                    
                    # COPY-ON-LOAD LOGIC:
                    # If temp file doesn't exist, copy from raw.
                    if not os.path.exists(temp_path):
                        if os.path.exists(raw_path):
                            print(f"Copying {filename} to temp: {raw_path} -> {temp_path}")
                            shutil.copy2(raw_path, temp_path)
                        else:
                            print(f"File not found in raw dir: {raw_path}")
                            continue
                    
                    # ALWAYS load from temp
                    load_source = temp_path
                    print(f"Loading {filename} from TEMP: {temp_path}")
                        
                    try:
                        points = np.load(load_source)
                        if points.size == 0: continue
                        
                        if len(points.shape) == 1:
                            points = points.reshape(-1, points.shape[0])
                            
                        N = points.shape[0]
                        nodes = np.zeros((N, 7))
                        edges = np.zeros((N - 1, 2), dtype=int)
                        
                        # Temp files should have 7 columns if edited, but might be raw copy (2 cols)
                        if points.shape[1] >= 7:
                            nodes[:, :] = points[:, 0:7]
                            nodes[:, 4] = i # Zone ID relative to this batch
                        else:
                            nodes[:, 1:3] = points[:, 0:2]
                            nodes[:, 4] = i
                            
                        # Assign IDs
                        current_lane_pids = []
                        for k in range(N):
                            nodes[k, 0] = current_pid + k
                            current_lane_pids.append(current_pid + k)
                        
                        # Edges - reconstruct sequentially
                        for k in range(N - 1):
                            edges[k, 0] = current_lane_pids[k]
                            edges[k, 1] = current_lane_pids[k + 1]
                            
                        loaded_nodes_list.append(nodes)
                        loaded_edges_list.append(edges)
                        loaded_names_list.append(filename)
                        
                        current_pid += N
                        
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
                
                if loaded_nodes_list:
                    new_nodes = np.vstack(loaded_nodes_list)
                    new_edges = np.vstack(loaded_edges_list)
                    new_names = loaded_names_list
                    
                    # Adjust Lane IDs (offset by existing max lane id)
                    new_nodes[:, 4] += lane_id_offset
                else:
                    new_nodes = np.array([])
                    new_edges = np.array([])
                    new_names = []

                if new_nodes.size > 0:
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
    # ... (unload logic remains mostly same, ensure save_temp_lanes is called)
    try:
        data = request.json
        filename = data.get('filename')

        if not filename:
            return jsonify({'status': 'error', 'message': 'No filename provided'}), 400

        # Save temp lanes (this might trigger splits or merges)
        split_map, merged_files = data_manager.save_temp_lanes(TEMP_LANES_DIR)
        
        # Identify files to remove: the file itself AND any split parts
        files_to_remove = [filename]
        
        # Also remove any files that were merged away during this save
        if merged_files:
            print(f"Files merged away: {merged_files}")
            for mf in merged_files:
                if mf not in files_to_remove:
                    files_to_remove.append(mf)
                
                # Delete from disk to prevent duplicate loading
                fpath = os.path.join(TEMP_LANES_DIR, mf)
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                        print(f"Deleted merged-away file from disk: {fpath}")
                    except Exception as e:
                        print(f"Error deleting merged file {fpath}: {e}")
        
        base_name, ext = os.path.splitext(filename)
        # Prefix is base_name + "_", e.g. "lane0_"
        # But we need to be careful not to match "lane0_1" with "lane0_10" if we just check prefix?
        # Actually, the logic in DataManager appends _{idx}.
        # So we look for files that start with f"{base_name}_" and end with ext.
        prefix = f"{base_name}_"
        
        # Look for derived files in currently loaded files
        for f in data_manager.file_names:
            if f and f.startswith(prefix) and f.endswith(ext):
                # Ensure it's a split part (digits after prefix)
                # e.g. lane0_1.npy. Suffix is "1".
                # lane0_1_1.npy. Suffix is "1_1"? No, base_name of lane0_1 is lane0_1.
                # So if we unload lane0, we want lane0_1, lane0_2.
                # If we unload lane0_1, we want lane0_1_1, lane0_1_2.
                # This prefix logic handles one level of recursion relative to the unloaded file.
                # But what if we unload lane0, and lane0_1_1 exists?
                # lane0_1_1 starts with lane0_. So it matches.
                # So recursively all descendants should be matched.
                if f not in files_to_remove:
                    files_to_remove.append(f)
        
        if len(files_to_remove) > 1:
            print(f"Unloading {filename} and its derived parts: {files_to_remove}")

        success = True
        for f in files_to_remove:
            if not data_manager.remove_file(f):
                # Don't fail completely if a part fails, but log it
                print(f"Failed to remove {f}")
                # If the main file fails, that's a problem, but we continue to try others

        # We consider success if at least the main file was processed (or attempted)
        # But remove_file returns False if file not found.
        # Let's return success if we finished the loop.
        
        return jsonify({
            'status': 'success',
            'nodes': data_manager.nodes.tolist(),
            'edges': data_manager.edges.tolist(),
            'file_names': [f for f in data_manager.file_names if f is not None],
            'debug_files_to_remove': files_to_remove
        })


    except Exception as e:
        print(f"Error unloading data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/reset_temp_file', methods=['POST'])
def reset_temp_file_endpoint():
    """Overwrite the temp file with the original raw file."""
    try:
        data = request.json
        filename = data.get('filename')
        raw_dir = data.get('raw_dir') # We need to know where the original is
        
        if not filename:
            return jsonify({'status': 'error', 'message': 'No filename provided'}), 400
            
        # Determine raw path
        if raw_dir:
             if os.path.isabs(raw_dir):
                raw_path = os.path.join(raw_dir, filename)
             else:
                raw_path = os.path.join(lanes_root, raw_dir, filename)
        else:
            # Fallback to current loader directory if not specified (might be risky if changed)
            raw_path = os.path.join(loader.directory, filename)

        temp_path = os.path.join(TEMP_LANES_DIR, filename)
        
        if os.path.exists(raw_path):
            # Ensure temp dir exists
            if not os.path.exists(TEMP_LANES_DIR):
                os.makedirs(TEMP_LANES_DIR)
                
            shutil.copy2(raw_path, temp_path)
            print(f"Reset temp file: {raw_path} -> {temp_path}")
            
            # Also delete any split parts (sub-lanes)
            # Pattern: filename_X.npy
            base_name, ext = os.path.splitext(filename)
            prefix = f"{base_name}_"
            
            deleted_parts = []
            if os.path.exists(TEMP_LANES_DIR):
                for f in os.listdir(TEMP_LANES_DIR):
                    if f.startswith(prefix) and f.endswith(ext):
                        # Check if it's a derived part (has digits after prefix)
                        # e.g. lane0_1.npy
                        part_path = os.path.join(TEMP_LANES_DIR, f)
                        try:
                            os.remove(part_path)
                            deleted_parts.append(f)
                        except Exception as e:
                            print(f"Error deleting split part {f}: {e}")
            
            if deleted_parts:
                print(f"Deleted split parts for {filename}: {deleted_parts}")
            
            return jsonify({'status': 'success', 'message': f'Reset temp file for {filename} and deleted {len(deleted_parts)} sub-lanes.'})
        else:
            return jsonify({'status': 'error', 'message': f'Original file not found at {raw_path}'}), 404
            
    except Exception as e:
        print(f"Error resetting temp file: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/operation', methods=['POST'])
def perform_operation():
    """Perform a specified operation on the data manager.
    
    This function handles various operations such as adding or deleting nodes and
    edges, applying updates, and managing the history of changes. It processes
    incoming JSON requests, executes the corresponding operation based on the
    provided parameters, and returns the updated state of nodes and edges. Error
    handling is implemented to manage exceptions and provide appropriate responses.
    
    Returns:
        Response: A JSON response containing the status of the operation and the current state of
            nodes and edges.
    """
    try:
        data = request.json
        operation = data.get('operation')
        params = data.get('params', {})

        if not operation:
            return jsonify({'status': 'error', 'message': 'No operation specified'}), 400

        if operation == 'add_node':
            x = params.get('x')
            y = params.get('y')
            lane_id = params.get('lane_id')
            connect_to = params.get('connect_to')
            
            new_id = data_manager.add_node(x, y, lane_id)
            if connect_to is not None and new_id is not None:
                data_manager.add_edge(connect_to, new_id)
                
        elif operation == 'add_edge':
            data_manager.add_edge(params.get('from_id'), params.get('to_id'))
            
        elif operation == 'delete_points':
            data_manager.delete_points(params.get('point_ids'))
            
        elif operation == 'break_links':
            data_manager.delete_edges_for_node(params.get('point_id'))
            
        elif operation == 'reverse_path':
            start_id = params.get('start_id')
            end_id = params.get('end_id')
            path = find_path(data_manager.edges, start_id, end_id)
            if path:
                data_manager.reverse_path(path)
            else:
                return jsonify({'status': 'error', 'message': 'No path found'}), 400
                
        elif operation == 'remove_between':
            start_id = params.get('start_id')
            end_id = params.get('end_id')
            path = find_path(data_manager.edges, start_id, end_id)
            if path:
                # Delete nodes strictly between start and end
                if len(path) > 2:
                    to_delete = path[1:-1]
                    data_manager.delete_points(to_delete)
            else:
                 return jsonify({'status': 'error', 'message': 'No path found'}), 400

        elif operation == 'copy_points':
            data_manager.copy_points(params.get('point_ids'))
            
        elif operation == 'batch_add_nodes':
            points = params.get('points')
            lane_id = params.get('lane_id')
            connect_id = params.get('connect_to_start_id')
            
            for pt in points:
                new_id = data_manager.add_node(pt['x'], pt['y'], lane_id)
                if connect_id is not None:
                    data_manager.add_edge(connect_id, new_id)
                connect_id = new_id # Chain them
                
        elif operation == 'apply_updates':
            nodes_data = params.get('nodes')
            edges_data = params.get('edges')
            if nodes_data:
                data_manager.nodes = np.array(nodes_data)
            if edges_data:
                data_manager.edges = np.array(edges_data)
            data_manager.sync_next_id()
            data_manager.history.append((data_manager.nodes.copy(), data_manager.edges.copy()))
            data_manager._auto_save_backup()

        elif operation == 'undo':
            data_manager.undo()
            
        elif operation == 'redo':
            data_manager.redo()

        else:
            return jsonify({'status': 'error', 'message': f'Unknown operation: {operation}'}), 400
        
        # Auto-save temp lanes after operation
        split_map, merged_files = data_manager.save_temp_lanes(TEMP_LANES_DIR)
        
        # Handle merged files (delete them)
        if merged_files:
            print(f"Files merged away during operation: {merged_files}")
            for mf in merged_files:
                fpath = os.path.join(TEMP_LANES_DIR, mf)
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                        print(f"Deleted merged-away file: {fpath}")
                    except Exception as e:
                        print(f"Error deleting merged file {fpath}: {e}")

        return jsonify({
            'status': 'success',
            'nodes': data_manager.nodes.tolist() if data_manager.nodes.size > 0 else [],
            'edges': data_manager.edges.tolist() if data_manager.edges.size > 0 else [],
            'message': f'Operation {operation} successful'
        })
    except Exception as e:
        print(f"Error performing operation {operation}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/smooth', methods=['POST'])
def smooth_path_endpoint():
    try:
        data = request.json
        start_id = data.get('start_id')
        end_id = data.get('end_id')
        smoothness = float(data.get('smoothness', 1.0))
        weight = float(data.get('weight', 0.5))

        if start_id is None or end_id is None:
            return jsonify({'status': 'error', 'message': 'Start and end IDs required'}), 400

        # Find path
        path_indices = find_path(data_manager.edges, start_id, end_id)
        if not path_indices:
             return jsonify({'status': 'error', 'message': 'No path found between selected nodes'}), 400

        # Get points
        # path_indices is list of IDs. We need to map to indices in data_manager.nodes?
        # No, data_manager.nodes is (N, 7). We need to find rows where col 0 is in path_indices.
        # But find_path returns IDs.
        
        # smooth_segment expects nodes array and path_ids
        smoothed_points = smooth_segment(data_manager.nodes, data_manager.edges, path_indices, smoothness, weight)
        
        if smoothed_points is None:
            return jsonify({'status': 'error', 'message': 'Smoothing failed'}), 400

        # Reconstruct full node data for preview
        preview_nodes = []
        # We assume smoothed_points corresponds 1-to-1 with path_indices
        for i, pid in enumerate(path_indices):
             # Find original node data
             node_mask = data_manager.nodes[:, 0] == pid
             if np.any(node_mask):
                 original_node = data_manager.nodes[node_mask][0].copy()
                 # Update X, Y
                 original_node[1] = smoothed_points[i][0]
                 original_node[2] = smoothed_points[i][1]
                 preview_nodes.append(original_node)

        return jsonify({
            'status': 'success',
            'updated_nodes': [n.tolist() for n in preview_nodes]
        })

    except Exception as e:
        print(f"Error smoothing path: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/unload_graph', methods=['POST'])
def unload_graph_endpoint():
    try:
        data_manager.clear_data()
        return jsonify({
            'status': 'success',
            'nodes': [],
            'edges': [],
            'file_names': []
        })
    except Exception as e:
        print(f"Error unloading graph: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/verify_yaw', methods=['POST'])
def verify_yaw_endpoint():
    try:
        nodes = data_manager.nodes
        edges = data_manager.edges
        
        if nodes.size == 0 or edges.size == 0:
             return jsonify({'status': 'success', 'results': []})

        # Create a map for quick node lookup
        # Node structure: [point_id, x, y, yaw, zone, width, indicator]
        node_map = {int(row[0]): row for row in nodes}
        
        results = []
        threshold = 0.4

        for edge in edges:
            u_id, v_id = int(edge[0]), int(edge[1])
            
            if u_id not in node_map or v_id not in node_map:
                continue
                
            u_node = node_map[u_id]
            v_node = node_map[v_id]
            
            # Calculate geometric yaw of the edge
            dx = v_node[1] - u_node[1]
            dy = v_node[2] - u_node[2]
            edge_yaw = np.arctan2(dy, dx)
            
            # Compare with stored yaw of the source node (u)
            stored_yaw = u_node[3]
            
            # Calculate diff
            diff = abs((((stored_yaw - edge_yaw) + np.pi) % (2 * np.pi)) - np.pi)
            
            status = 'aligned' if diff < threshold else 'misaligned'
            
            results.append({
                'u': u_id,
                'v': v_id,
                'status': status,
                'diff': float(diff)
            })

        return jsonify({
            'status': 'success',
            'results': results
        })

    except Exception as e:
        print(f"Error verifying yaw: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
