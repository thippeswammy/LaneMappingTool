import os
import shutil
import time
import numpy as np
import pickle
import networkx as nx


class DataManager:
    def __init__(self, nodes, edges, file_names):
        self.nodes = nodes
        self.edges = edges
        self.file_names = file_names

        if self.nodes.size > 0:
            self._next_point_id = int(np.max(self.nodes[:, 0])) + 1
        else:
            self._next_point_id = 0

        self.history = [(self.nodes.copy(), self.edges.copy())]
        self.redo_stack = []

        self.last_backup = time.time()
        self.backup_interval = 300  # 5 minutes

        print(f"DataManager initialized with {len(self.nodes)} nodes and {len(self.edges)} edges.")

    def _get_new_point_id(self):
        new_id = self._next_point_id
        self._next_point_id += 1
        return new_id

    def add_node(self, x, y, original_lane_id):
        try:
            new_point_id = self._get_new_point_id()
            new_node = np.array([[new_point_id, x, y, 0.0, original_lane_id]])

            if self.nodes.size > 0:
                self.nodes = np.vstack([self.nodes, new_node])
            else:
                self.nodes = new_node

            self.history.append((self.nodes.copy(), self.edges.copy()))
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Added node {new_point_id}: ({x:.2f}, {y:.2f}, lane_id={original_lane_id})")
            return new_point_id

        except Exception as e:
            print(f"Error adding node: {e}")
            return None

    def add_edge(self, from_point_id, to_point_id):
        try:
            if np.any((self.edges[:, 0] == from_point_id) & (self.edges[:, 1] == to_point_id)):
                print(f"Edge from {from_point_id} to {to_point_id} already exists.")
                return

            new_edge = np.array([[from_point_id, to_point_id]], dtype=int)

            if self.edges.size > 0:
                self.edges = np.vstack([self.edges, new_edge])
            else:
                self.edges = new_edge

            from_node_mask = self.nodes[:, 0] == from_point_id
            to_node_mask = self.nodes[:, 0] == to_point_id

            if np.any(from_node_mask) and np.any(to_node_mask):
                from_node = self.nodes[from_node_mask][0]
                to_node = self.nodes[to_node_mask][0]

                dx = to_node[1] - from_node[1]  # x_to - x_from
                dy = to_node[2] - from_node[2]  # y_to - y_from
                yaw = np.arctan2(dy, dx)
                self.nodes[from_node_mask, 3] = yaw

            self.history.append((self.nodes.copy(), self.edges.copy()))
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Added edge from {from_point_id} to {to_point_id}")

        except Exception as e:
            print(f"Error adding edge: {e}")

    def delete_points(self, point_ids_to_delete):
        if not point_ids_to_delete:
            return
        try:
            point_ids = np.asarray(point_ids_to_delete, dtype=int)

            node_mask = ~np.isin(self.nodes[:, 0], point_ids)
            self.nodes = self.nodes[node_mask]

            if self.edges.size > 0:
                edge_mask_from = ~np.isin(self.edges[:, 0], point_ids)
                edge_mask_to = ~np.isin(self.edges[:, 1], point_ids)
                edge_mask_combined = edge_mask_from & edge_mask_to
                self.edges = self.edges[edge_mask_combined]

            self.history.append((self.nodes.copy(), self.edges.copy()))
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Deleted {len(point_ids)} nodes and associated edges")

        except Exception as e:
            print(f"Error deleting points: {e}")

    def change_ids(self, point_ids, new_original_lane_id):
        if not point_ids:
            return
        try:
            point_ids = np.asarray(point_ids, dtype=int)
            node_mask = np.isin(self.nodes[:, 0], point_ids)

            if np.any(node_mask):
                self.nodes[node_mask, 4] = new_original_lane_id
                self.history.append((self.nodes.copy(), self.edges.copy()))
                self.redo_stack = []
                self._auto_save_backup()
                print(f"Changed original lane ID for {np.sum(node_mask)} nodes to {new_original_lane_id}")
            else:
                print("No matching nodes found to change ID.")

        except Exception as e:
            print(f"Error changing IDs: {e}")

    def remove_points_above(self, index, lane_id):
        print("Function 'remove_points_above' is not implemented for graph model.")
        pass

    def remove_points_below(self, index, lane_id):
        print("Function 'remove_points_below' is not implemented for graph model.")
        pass

    def merge_lanes(self, *args):
        print("Function 'merge_lanes' is obsolete. Use 'add_edge(from_id, to_id)' instead.")
        pass

    def _create_networkx_graph(self):
        G = nx.DiGraph()
        if self.nodes.size > 0:
            for node_data in self.nodes:
                point_id = int(node_data[0])
                G.add_node(
                    point_id,
                    x=node_data[1],
                    y=node_data[2],
                    yaw=node_data[3],
                    original_lane_id=int(node_data[4])
                )
        if self.edges.size > 0:
            for edge_data in self.edges:
                G.add_edge(int(edge_data[0]), int(edge_data[1]))
        return G

    def save_all_lanes(self):
        folder = "workspace-Temp"
        try:
            os.makedirs(folder, exist_ok=True)
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

            nodes_filename = os.path.join(folder, "graph_nodes.npy")
            edges_filename = os.path.join(folder, "graph_edges.npy")
            np.save(nodes_filename, self.nodes)
            np.save(edges_filename, self.edges)
            print(f"Saved graph nodes to {nodes_filename}")
            print(f"Saved graph edges to {edges_filename}")

            G = self._create_networkx_graph()
            pickle_file_path = os.path.join(folder, "output.pickle")
            with open(pickle_file_path, "wb") as f:
                pickle.dump(G, f)
            print(f"Saved NetworkX graph to {pickle_file_path}")

        except Exception as e:
            print(f"Error saving graph data to temp: {e}")

    # --- FUNCTIONS BELOW WERE MISSING ---

    def clear_data(self):
        try:
            self.nodes = np.array([])
            self.edges = np.array([])
            self.history = [(np.array([]), np.array([]))]
            self.redo_stack = []
            self.file_names = []
            self._next_point_id = 0
            self._auto_save_backup()
            print("Cleared all nodes and edges")
        except Exception as e:
            print(f"Error clearing data: {e}")

    def undo(self):
        try:
            if len(self.history) <= 1:
                print("Nothing to undo")
                return self.nodes, self.edges, False

            self.redo_stack.append(self.history.pop())

            nodes_copy, edges_copy = self.history[-1]
            self.nodes = nodes_copy.copy()
            self.edges = edges_copy.copy()

            self._auto_save_backup()
            print("Undo performed")  # Added print statement for confirmation
            return self.nodes, self.edges, True

        except Exception as e:
            print(f"Error during undo: {e}")
            return self.nodes, self.edges, False

    def redo(self):
        try:
            if not self.redo_stack:
                print("Nothing to redo")
                return self.nodes, self.edges, False

            nodes_copy, edges_copy = self.redo_stack.pop()
            self.nodes = nodes_copy.copy()
            self.edges = edges_copy.copy()

            self.history.append((self.nodes.copy(), self.edges.copy()))

            self._auto_save_backup()
            print("Redo performed")  # Added print statement for confirmation
            return self.nodes, self.edges, True

        except Exception as e:
            print(f"Error during redo: {e}")
            return self.nodes, self.edges, False

    # --- END OF MISSING FUNCTIONS ---

    def save(self):
        try:
            os.makedirs("./files", exist_ok=True)
            nodes_filename = "./files/WorkingNodes.npy"
            edges_filename = "./files/WorkingEdges.npy"

            np.save(nodes_filename, self.nodes)
            np.save(edges_filename, self.edges)

            print(f"Saved nodes to {nodes_filename}")
            print(f"Saved edges to {edges_filename}")
            self._auto_save_backup()

            G = self._create_networkx_graph()
            pickle_file_path = r"./files/output.pickle"
            with open(pickle_file_path, "wb") as f:
                pickle.dump(G, f)

            print(f"Saved NetworkX graph to {pickle_file_path}")

            return nodes_filename

        except Exception as e:
            print(f"Error saving data: {e}")
            return None

    def _auto_save_backup(self):
        try:
            if time.time() - self.last_backup < self.backup_interval:
                return

            os.makedirs("workspace-Backup", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            nodes_filename = os.path.join("workspace-Backup", f"backup_nodes_{timestamp}.npy")
            edges_filename = os.path.join("workspace-Backup", f"backup_edges_{timestamp}.npy")

            if self.nodes.size > 0:
                np.save(nodes_filename, self.nodes)
                np.save(edges_filename, self.edges)
                print(f"Auto-saved backup nodes and edges to {timestamp}")

            self.last_backup = time.time()
        except Exception as e:
            print(f"Backup failed: {e}")