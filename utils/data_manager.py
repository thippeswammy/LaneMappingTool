import math
import os
import pickle
import time

import networkx as nx
import numpy as np


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
            # Node: [point_id, x, y, yaw, zone, width, indicator]
            # original_lane_id maps to zone
            new_node = np.array([[new_point_id, x, y, 0.0, original_lane_id, 0.0, 0.0]])

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

    def _update_yaws(self, edge_pairs):
        """Update yaws for a list of (from_id, to_id) pairs."""
        for from_id, to_id in edge_pairs:
            from_node_mask = self.nodes[:, 0] == from_id
            to_node_mask = self.nodes[:, 0] == to_id

            if np.any(from_node_mask) and np.any(to_node_mask):
                from_node = self.nodes[from_node_mask][0]
                to_node = self.nodes[to_node_mask][0]

                dx = to_node[1] - from_node[1]  # x_to - x_from
                dy = to_node[2] - from_node[2]  # y_to - y_from
                yaw = np.arctan2(dy, dx)
                self.nodes[from_node_mask, 3] = yaw

    def reverse_path(self, path_ids):
        """Reverse the direction of all edges along a given path of node IDs.
        
        This function takes a list of node IDs and reverses the edges between them.  It
        first checks if the path contains at least two nodes, then identifies the
        edges to be deleted and the corresponding edges to be added in reverse. A  mask
        is created to filter out the edges that need to be deleted, and the new  edges
        are added to the existing edges. Finally, it updates the yaws for the  new
        "from" nodes and saves the current state to history for potential undo
        operations.
        
        Args:
            path_ids (list): A list of node IDs representing the path.
        """
        try:
            edges_to_delete = []
            edges_to_add = []

            # Create a fast lookup set of all existing edges
            existing_edges = set()
            for edge in self.edges:
                existing_edges.add((edge[0], edge[1]))

            for i in range(len(path_ids) - 1):
                A = path_ids[i]
                B = path_ids[i + 1]

                # Check which direction the edge currently exists in
                if (A, B) in existing_edges:
                    # Forward edge exists (A -> B), reverse it
                    edges_to_delete.append((A, B))
                    edges_to_add.append((B, A))
                elif (B, A) in existing_edges:
                    # Backward edge exists (B -> A), reverse it
                    edges_to_delete.append((B, A))
                    edges_to_add.append((A, B))
                else:
                    print(f"Warning: No edge found between {A} and {B} in either direction. Path is broken.")

            if not edges_to_delete:
                print("No matching edges found to reverse.")
                return

            # Build a mask to keep all edges *except* the ones we're deleting
            keep_mask = np.ones(len(self.edges), dtype=bool)

            edges_to_delete_set = set(edges_to_delete)
            for i in range(len(self.edges)):
                if (self.edges[i, 0], self.edges[i, 1]) in edges_to_delete_set:
                    keep_mask[i] = False

            # Apply the mask
            self.edges = self.edges[keep_mask]

            # Add the new reversed edges
            if edges_to_add:
                edges_to_add_np = np.array(edges_to_add, dtype=int)
                self.edges = np.vstack([self.edges, edges_to_add_np])

            # Update the yaws for the new "from" nodes
            self._update_yaws(edges_to_add)

            # Save to history
            self.history.append((self.nodes.copy(), self.edges.copy()))
            self.redo_stack = []
            self._auto_save_backup()

            print(f"Reversed {len(edges_to_add)} edges in path.")

        except Exception as e:
            print(f"Error reversing path: {e}")

    def delete_points(self, point_ids_to_delete):
        """Delete specified points and their associated edges from the graph."""
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
                # Update zone (col 4)
                self.nodes[node_mask, 4] = new_original_lane_id
                self.history.append((self.nodes.copy(), self.edges.copy()))
                self.redo_stack = []
                self._auto_save_backup()
                print(f"Changed zone (original lane ID) for {np.sum(node_mask)} nodes to {new_original_lane_id}")
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
        """
        Creates a NetworkX graph with:
        Node: t (point_id), x, y, yaw, zone=0, width=0, indicator=0
        Edge: weight=EuclideanDistance
        """
        G = nx.DiGraph()

        node_coords = {}

        if self.nodes.size > 0:
            for node_data in self.nodes:
                t = int(node_data[0])
                x = node_data[1]
                y = node_data[2]
                yaw = node_data[3]
                zone = node_data[4]
                width = node_data[5]
                indicator = node_data[6]

                node_coords[t] = (x, y)

                G.add_node(
                    t,
                    x=x,
                    y=y,
                    yaw=yaw,
                    zone=zone,
                    width=width,
                    indicator=indicator
                )

        if self.edges.size > 0:
            for edge_data in self.edges:
                u = int(edge_data[0])
                v = int(edge_data[1])

                # Calculate weight (Euclidean distance)
                weight = 1.0
                if u in node_coords and v in node_coords:
                    x1, y1 = node_coords[u]
                    x2, y2 = node_coords[v]
                    weight = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

                G.add_edge(u, v, weight=weight)

        return G

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
            print("Undo performed")
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
            print("Redo performed")
            return self.nodes, self.edges, True

        except Exception as e:
            print(f"Error during redo: {e}")
            return self.nodes, self.edges, False

    def save_by_matplotlib(self):
        """Save nodes and edges to files and create a backup."""
        try:
            os.makedirs("./files", exist_ok=True)
            nodes_filename = "./files/graph_nodes.npy"
            edges_filename = "./files/graph_edges.npy"

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

    def save_by_web(self):
        """Save nodes and edges to files and create a backup."""
        folder = "workspace"
        try:
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
            print(f"Error saving data: {e}")
            return None

    # def renumber_all_nodes(self):
    #     """
    #     Renumbers all node point_ids to be sequential (0 to N-1).
    #     This is a destructive operation that clears the undo/redo history.
    #     """
    #     try:
    #         N = len(self.nodes)
    #         if N == 0:
    #             print("No nodes to renumber.")
    #             return
    #
    #         old_ids = self.nodes[:, 0].copy()
    #         new_ids = np.arange(N)
    #
    #         # Create a fast lookup map {old_id: new_id}
    #         id_map = {old: new for old, new in zip(old_ids, new_ids)}
    #
    #         # Update nodes array
    #         self.nodes[:, 0] = new_ids
    #
    #         # Update edges array using the map
    #         vectorized_map = np.vectorize(id_map.get)
    #
    #         if self.edges.size > 0:
    #             self.edges[:, 0] = vectorized_map(self.edges[:, 0])
    #             self.edges[:, 1] = vectorized_map(self.edges[:, 1])
    #
    #         # Reset the next_point_id counter
    #         self._next_point_id = N
    #
    #         # Clear history
    #         self.history = [(self.nodes.copy(), self.edges.copy())]
    #         self.redo_stack = []
    #
    #         print("Renumbered all nodes. Undo/redo history has been cleared.")
    #
    #     except Exception as e:
    #         print(f"Error during renumbering: {e}")

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

    def delete_edges_for_node(self, point_id):
        if self.edges.size == 0:
            return

        try:
            # Create a mask for edges to *delete*
            # delete_mask = (self.edges[:, 0] == point_id) | (self.edges[:, 1] == point_id)
            delete_mask = (self.edges[:, 1] == point_id)
            # Mask for edges to *keep* is the inverse
            keep_mask = ~delete_mask
            deleted_count = np.sum(delete_mask)
            if deleted_count > 0:
                self.edges = self.edges[keep_mask]
                self.history.append((self.nodes.copy(), self.edges.copy()))
                self.redo_stack = []
                self._auto_save_backup()
                print(f"Deleted {deleted_count} edges for node {point_id}")
            else:
                print(f"No edges found for node {point_id}")

        except Exception as e:
            print(f"Error deleting edges: {e}")
