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

        self.history = [(self.nodes.copy(), self.edges.copy(), list(self.file_names))]
        self.redo_stack = []

        self.last_backup = time.time()
        self.backup_interval = 300  # 5 minutes

        print(f"DataManager initialized with {len(self.nodes)} nodes and {len(self.edges)} edges.")

    def _get_new_point_id(self):
        new_id = self._next_point_id
        self._next_point_id += 1
        return new_id

    def add_node(self, x, y, original_lane_id):
        """Adds a new node to the graph with specified coordinates and lane ID."""
        try:
            new_point_id = self._get_new_point_id()
            # Node: [point_id, x, y, yaw, zone, width, indicator]
            # original_lane_id maps to zone
            new_node = np.array([[new_point_id, x, y, 0.0, original_lane_id, 0.0, 0.0]])

            if self.nodes.size > 0:
                self.nodes = np.vstack([self.nodes, new_node])
            else:
                self.nodes = new_node

            self.history.append((self.nodes.copy(), self.edges.copy(), list(self.file_names)))
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Added node {new_point_id}: ({x:.2f}, {y:.2f}, lane_id={original_lane_id})")
            return new_point_id

        except Exception as e:
            print(f"Error adding node: {e}")
            return None

    def add_edge(self, from_point_id, to_point_id):
        """Add an edge between two points in the graph.
        
        This method adds an edge from `from_point_id` to `to_point_id` in the graph's
        edge list.  It first checks if the edge already exists and reshapes the edges
        array if necessary.  If both nodes exist, it calculates the yaw angle between
        them and updates the corresponding  node's yaw value. The current state of
        nodes and edges is then saved to history, and a  backup is created
        automatically.
        
        Args:
            from_point_id: The identifier for the starting point of the edge.
            to_point_id: The identifier for the ending point of the edge.
        """
        try:
            if self.edges.size > 0:
                if self.edges.ndim == 1:
                     self.edges = self.edges.reshape(-1, 2)
                if np.any((self.edges[:, 0] == from_point_id) & (self.edges[:, 1] == to_point_id)):
                    print(f"Edge from {from_point_id} to {to_point_id} already exists.")
                    return

                new_edge = np.array([[from_point_id, to_point_id]], dtype=int)
                self.edges = np.vstack([self.edges, new_edge])
            else:
                self.edges = np.array([[from_point_id, to_point_id]], dtype=int)

            from_node_mask = self.nodes[:, 0] == from_point_id
            to_node_mask = self.nodes[:, 0] == to_point_id

            if np.any(from_node_mask) and np.any(to_node_mask):
                from_node = self.nodes[from_node_mask][0]
                to_node = self.nodes[to_node_mask][0]

                dx = to_node[1] - from_node[1]  # x_to - x_from
                dy = to_node[2] - from_node[2]  # y_to - y_from
                yaw = np.arctan2(dy, dx)
                self.nodes[from_node_mask, 3] = yaw

            self.history.append((self.nodes.copy(), self.edges.copy(), list(self.file_names)))
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
        
        This function takes a list of node IDs and reverses the edges between them. It
        first checks if the path contains at least two nodes, then identifies the edges
        to be deleted and the corresponding edges to be added in reverse. A mask is
        created to filter out the edges that need to be deleted, and the new edges are
        added to the existing edges. Finally, it updates the yaws for the new "from"
        nodes and saves the current state to history for potential undo operations.
        
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
            self.history.append((self.nodes.copy(), self.edges.copy(), list(self.file_names)))
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

            self.history.append((self.nodes.copy(), self.edges.copy(), list(self.file_names)))
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Deleted {len(point_ids)} nodes and associated edges")

        except Exception as e:
            print(f"Error deleting points: {e}")

    def copy_points(self, point_ids_to_copy):
        """Copy specified points and their internal edges.
        
        This function copies nodes identified by `point_ids_to_copy`, creating new
        nodes with updated IDs and adjusted positions. It also copies edges that
        connect the selected nodes, ensuring that both endpoints of the edges are
        included in the copy process. The function maintains a history of changes and
        performs an automatic backup after the operation.
        
        Args:
            point_ids_to_copy (list): A list of point IDs to be copied.
        """
        if not point_ids_to_copy:
            return
        try:
            point_ids = set(point_ids_to_copy)
            
            # Find nodes to copy
            node_mask = np.isin(self.nodes[:, 0], list(point_ids))
            nodes_to_copy = self.nodes[node_mask]
            
            if nodes_to_copy.size == 0:
                print("No nodes found to copy.")
                return

            # Map old IDs to new IDs
            id_map = {}
            new_nodes_list = []
            
            offset_x = 2.0
            offset_y = 2.0

            for node in nodes_to_copy:
                old_id = int(node[0])
                new_id = self._get_new_point_id()
                id_map[old_id] = new_id
                
                new_node = node.copy()
                new_node[0] = new_id
                new_node[1] += offset_x # X
                new_node[2] += offset_y # Y
                
                new_nodes_list.append(new_node)

            if not new_nodes_list:
                return

            # Add new nodes
            new_nodes_arr = np.array(new_nodes_list)
            self.nodes = np.vstack([self.nodes, new_nodes_arr])

            # Copy edges where both endpoints are in the selection
            new_edges_list = []
            if self.edges.size > 0:
                for edge in self.edges:
                    u, v = int(edge[0]), int(edge[1])
                    if u in point_ids and v in point_ids:
                        if u in id_map and v in id_map:
                            new_u = id_map[u]
                            new_v = id_map[v]
                            new_edges_list.append([new_u, new_v])
            
            if new_edges_list:
                new_edges_arr = np.array(new_edges_list)
                self.edges = np.vstack([self.edges, new_edges_arr])

            self.history.append((self.nodes.copy(), self.edges.copy(), list(self.file_names)))
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Copied {len(nodes_to_copy)} nodes and {len(new_edges_list)} edges.")

        except Exception as e:
            print(f"Error copying points: {e}")

    def change_ids(self, point_ids, new_original_lane_id):
        if not point_ids:
            return
        try:
            point_ids = np.asarray(point_ids, dtype=int)
            node_mask = np.isin(self.nodes[:, 0], point_ids)

            if np.any(node_mask):
                # Update zone (col 4)
                self.nodes[node_mask, 4] = new_original_lane_id
                self.history.append((self.nodes.copy(), self.edges.copy(), list(self.file_names)))
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
        """Reverts the last action in the history."""
        try:
            if len(self.history) <= 1:
                print("Nothing to undo")
                return self.nodes, self.edges, False

            self.redo_stack.append(self.history.pop())

            # Handle both 2-item (old) and 3-item (new) history tuples
            state = self.history[-1]
            if len(state) == 3:
                nodes_copy, edges_copy, file_names_copy = state
                self.file_names = list(file_names_copy)
            else:
                nodes_copy, edges_copy = state
                # Keep existing file_names if not in history (fallback)

            self.nodes = nodes_copy.copy()
            self.edges = edges_copy.copy()

            self._auto_save_backup()
            print("Undo performed")
            return self.nodes, self.edges, True

        except Exception as e:
            print(f"Error during undo: {e}")
            return self.nodes, self.edges, False

    def redo(self):
        """Reapplies the last action from the redo stack."""
        try:
            if not self.redo_stack:
                print("Nothing to redo")
                return self.nodes, self.edges, False

            state = self.redo_stack.pop()
            self.history.append(state)

            if len(state) == 3:
                nodes_copy, edges_copy, file_names_copy = state
                self.file_names = list(file_names_copy)
            else:
                nodes_copy, edges_copy = state

            self.nodes = nodes_copy.copy()
            self.edges = edges_copy.copy()

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

    def save_by_web(self, folder="workspace"):
        """Save nodes and edges to files and create a backup."""
        if not os.path.exists(folder):
            os.makedirs(folder)
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
    def remove_file(self, filename):
        """Remove all nodes and edges associated with a specific file (zone)."""
        try:
            if filename not in self.file_names:
                print(f"File {filename} not found in loaded files.")
                return False

            # Find the index (zone ID) of the file
            # Note: We must find the *original* index, even if we've replaced some with None.
            # But here we assume file_names tracks the zones.
            try:
                zone_id = self.file_names.index(filename)
            except ValueError:
                print(f"File {filename} not found in file_names list.")
                return False

            print(f"Removing file {filename} (Zone {zone_id})...")

            # Identify nodes to remove
            nodes_to_remove_mask = self.nodes[:, 4] == zone_id
            nodes_to_remove_ids = self.nodes[nodes_to_remove_mask, 0]

            if nodes_to_remove_ids.size == 0:
                print(f"No nodes found for zone {zone_id}. Just removing filename.")
                self.file_names[zone_id] = None # Mark as removed
                return True

            # Remove nodes
            self.nodes = self.nodes[~nodes_to_remove_mask]

            # Remove edges connected to these nodes
            if self.edges.size > 0:
                edge_mask_from = np.isin(self.edges[:, 0], nodes_to_remove_ids)
                edge_mask_to = np.isin(self.edges[:, 1], nodes_to_remove_ids)
                edge_mask_delete = edge_mask_from | edge_mask_to
                self.edges = self.edges[~edge_mask_delete]

            # Mark file as removed in the list to preserve indices for other zones
            self.file_names[zone_id] = None

            self.history.append((self.nodes.copy(), self.edges.copy()))
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Successfully removed file {filename}.")
            return True

        except Exception as e:
            print(f"Error removing file {filename}: {e}")
            return False

    def merge_connected_lanes(self):
        """
        Identify edges connecting different zones and merge them.
        Returns a list of filenames that were merged away (and should be deleted).
        """
        if self.edges.size == 0 or self.nodes.size == 0:
            return []

        merged_files = []
        
        # Iterate until no more merges occur (transitive merges)
        while True:
            merged_in_pass = False
            
            # Create a map of point_id to zone_id for quick lookup
            # nodes column 0 is point_id, column 4 is zone_id
            point_to_zone = {int(row[0]): int(row[4]) for row in self.nodes}
            
            # Check each edge
            for edge in self.edges:
                u, v = int(edge[0]), int(edge[1])
                
                if u not in point_to_zone or v not in point_to_zone:
                    continue
                    
                zone_u = point_to_zone[u]
                zone_v = point_to_zone[v]
                
                if zone_u != zone_v:
                    # Found a connection between different zones! Merge them.
                    # Merge the higher zone ID into the lower one (usually keeps the original file)
                    # Exception: if one is None (shouldn't happen for active nodes)
                    
                    target_zone = min(zone_u, zone_v)
                    source_zone = max(zone_u, zone_v)
                    
                    # Update nodes
                    self.nodes[self.nodes[:, 4] == source_zone, 4] = target_zone
                    
                    # Record the file to be deleted
                    if source_zone < len(self.file_names):
                        fname = self.file_names[source_zone]
                        if fname and fname not in merged_files:
                            merged_files.append(fname)
                        
                        # Mark as removed in file_names
                        self.file_names[source_zone] = None
                        
                    print(f"Merged Zone {source_zone} into Zone {target_zone}")
                    merged_in_pass = True
                    break # Restart loop to refresh point_to_zone map
            
            if not merged_in_pass:
                break
                
        return merged_files

    def split_disconnected_lanes(self):
        """Check each zone (lane) for disconnected components and manage zone IDs.
        
        The function iterates through unique zones, builds a graph for each zone, and
        identifies connected components. If a zone is split into multiple components,
        it retains the largest component's original zone ID and filename while
        assigning new IDs and filenames to the smaller components. A dictionary mapping
        original filenames to lists of new filenames is returned.
        
        Returns:
            dict: A mapping of original filename to a list of new filenames created.
        """
        try:
            split_map = {} # {original_filename: [new_filename1, new_filename2]}
            
            if self.nodes.size == 0:
                return split_map

            unique_zones = np.unique(self.nodes[:, 4]).astype(int)
            changes_made = False
            
            # We need to iterate over a copy because we might append to unique_zones implicitly by adding new zones
            # But actually we just need to process the current set of zones.
            
            # Map edges to zones for faster lookup
            # An edge belongs to a zone if both its nodes belong to that zone.
            # If nodes are in different zones, it's a connection between lanes, not *in* the lane.
            
            for zone_id in unique_zones:
                if zone_id >= len(self.file_names) or self.file_names[zone_id] is None:
                    continue

                filename = self.file_names[zone_id]
                
                # Get nodes in this zone
                zone_mask = self.nodes[:, 4] == zone_id
                zone_node_ids = self.nodes[zone_mask, 0]
                
                if len(zone_node_ids) < 2:
                    continue

                # Build a graph for this zone
                G = nx.Graph() # Undirected for connectivity check
                G.add_nodes_from(zone_node_ids)
                
                # Add edges that are purely within this zone
                if self.edges.size > 0:
                    # Vectorized check is hard, let's just iterate relevant edges
                    # Optimization: Filter edges where both u and v are in zone_node_ids
                    # This might be slow if many edges. 
                    # Faster: 
                    mask_u = np.isin(self.edges[:, 0], zone_node_ids)
                    mask_v = np.isin(self.edges[:, 1], zone_node_ids)
                    zone_edges = self.edges[mask_u & mask_v]
                    
                    for edge in zone_edges:
                        G.add_edge(edge[0], edge[1])
                
                # Find connected components
                components = list(nx.connected_components(G))
                
                if len(components) > 1:
                    print(f"Zone {zone_id} ({filename}) is split into {len(components)} parts.")
                    changes_made = True
                    
                    # Sort by size (descending)
                    components.sort(key=len, reverse=True)
                    
                    # Largest component keeps the original zone_id and filename
                    # Others get new zones
                    
                    base_name, ext = os.path.splitext(filename)
                    
                    new_parts = []
                    
                    for i in range(1, len(components)):
                        comp_nodes = components[i]
                        new_zone_id = len(self.file_names)
                        
                        # Generate new filename
                        # Try to find a unique name
                        part_idx = 1
                        while True:
                            new_filename = f"{base_name}_{part_idx}{ext}"
                            if new_filename not in self.file_names:
                                break
                            part_idx += 1
                        
                        self.file_names.append(new_filename)
                        new_parts.append(new_filename)
                        
                        # Update nodes to new zone_id
                        comp_mask = np.isin(self.nodes[:, 0], list(comp_nodes))
                        self.nodes[comp_mask, 4] = new_zone_id
                        
                        print(f"  Moved {len(comp_nodes)} nodes to new zone {new_zone_id} ({new_filename})")
                    
                    if new_parts:
                        split_map[filename] = new_parts
            
            # if changes_made:
            #     self.history.append((self.nodes.copy(), self.edges.copy()))
            #     self.redo_stack = []
            #     self._auto_save_backup()
                
            return split_map

        except Exception as e:
            print(f"Error splitting disconnected lanes: {e}")
            return {}

    def save_temp_lanes(self, output_dir):
        """Save each lane (zone) to a separate .npy file in the output directory."""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 1. Merge connected lanes first
            merged_files = self.merge_connected_lanes()

            # 2. Check for splits
            split_map = self.split_disconnected_lanes()

            # Identify unique zones
            if self.nodes.size == 0:
                return split_map, merged_files

            unique_zones = np.unique(self.nodes[:, 4]).astype(int)

            for zone_id in unique_zones:
                # Get filename for this zone
                if zone_id < len(self.file_names):
                    filename = self.file_names[zone_id]
                    if filename is None:
                        continue # Skip removed files
                else:
                    # Fallback if file_names is out of sync (shouldn't happen if managed correctly)
                    filename = f"temp_lane_{zone_id}.npy"

                # Extract nodes for this zone
                zone_mask = self.nodes[:, 4] == zone_id
                zone_nodes = self.nodes[zone_mask]

                # Save full node data (7 columns)
                # [point_id, x, y, yaw, zone, width, indicator]
                save_path = os.path.join(output_dir, filename)
                np.save(save_path, zone_nodes)
                print(f"Saved temp file for {filename} to {save_path}")
            
            # Cleanup stale split files
            # If a file exists in output_dir that looks like a split part of an active file
            # but is NOT in self.file_names, it is stale (e.g. from Undo).
            try:
                existing_files = os.listdir(output_dir)
                active_files = set([f for f in self.file_names if f is not None])
                
                for fname in existing_files:
                    if fname not in active_files and fname.endswith(".npy"):
                        # Check if it is a split part of an active file
                        for active_file in active_files:
                            active_base = os.path.splitext(active_file)[0]
                            if fname.startswith(active_base + "_"):
                                print(f"Deleting stale split file: {fname}")
                                try:
                                    os.remove(os.path.join(output_dir, fname))
                                except OSError as e:
                                    print(f"Error deleting {fname}: {e}")
                                break
            except Exception as e:
                print(f"Error cleaning up stale files: {e}")

            return split_map, merged_files

        except Exception as e:
            print(f"Error saving temp lanes: {e}")
            return {}, []

