import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np

# Adjust path to import from the parent project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.data_loader import DataLoader
from utils.data_manager import DataManager
from web.backend.curve_utils import find_path, smooth_segment

# --- App Setup ---
app = Flask(__name__)
CORS(app)

# --- Data Loading ---
base_dir = os.path.dirname(os.path.abspath(__file__))
# Data is expected to be in lanes/TEMP1 relative to project root
data_path = os.path.join(base_dir, '../../lanes/TEMP1')

if not os.path.isdir(data_path):
    os.makedirs(data_path)
    print(f"Created data directory at: {data_path}")
else:
    print(f"Loading data from: {data_path}")


loader = DataLoader(data_path)
nodes, edges, file_names = loader.load_data()
data_manager = DataManager(nodes, edges, file_names)

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

        data_manager.save_all_lanes()

        return jsonify({'status': 'success', 'message': 'Data saved successfully.'})
    except Exception as e:
        print(f"Error saving data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/smooth', methods=['POST'])
def smooth_path_endpoint():
    try:
        data = request.get_json()
        start_id = int(data.get('start_id'))
        end_id = int(data.get('end_id'))
        smoothness = float(data.get('smoothness', 1.0))
        weight = float(data.get('weight', 20))

        path_ids = find_path(data_manager.edges, start_id, end_id)
        if not path_ids:
            return jsonify({'status': 'error', 'message': 'No path found between nodes.'}), 404

        new_points_xy = smooth_segment(data_manager.nodes, data_manager.edges, path_ids, smoothness, weight)
        if new_points_xy is None:
            return jsonify({'status': 'error', 'message': 'Smoothing failed. Path may be too short, contain duplicates, or be invalid for B-Spline.'}), 400
        
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
                    dx = new_points_xy[i+1, 0] - new_points_xy[i, 0]
                    dy = new_points_xy[i+1, 1] - new_points_xy[i, 1]
                    new_node[3] = np.arctan2(dy, dx)
                elif i > 0:
                    # Last point inherits yaw from the previous one in the preview
                    new_node[3] = updated_nodes_preview[i-1][3]

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
            if params.get('connect_to') is not None:
                data_manager.add_edge(params['connect_to'], new_node_id)

        elif operation == 'add_edge':
            from_id, to_id = params['from_id'], params['to_id']
            data_manager.add_edge(from_id, to_id)
            
        elif operation == 'delete_points':
            point_ids = params['point_ids']
            data_manager.delete_points(point_ids)
            
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