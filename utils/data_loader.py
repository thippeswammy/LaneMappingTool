import os

import numpy as np


class DataLoader:
    def __init__(self, directory, file_order=None):
        """
        directory   : folder containing .npy files
        file_order  : optional list of filenames (or partial names) to enforce order
        """
        if not os.path.isdir(directory):
            raise ValueError(f"Directory does not exist: {directory}")
        self.directory = directory
        self.D = None
        self.file_order = file_order

    def load_graph_data(self, nodes_path, edges_path):
        """
        Loads existing graph state (nodes and edges) from specific paths.
        Distinguishes between raw point data and processed graph data.
        """
        nodes = np.array([])
        edges = np.array([])
        file_names = []
        D = 1.0

        if os.path.exists(nodes_path) and os.path.exists(edges_path):
            print(f"Loading saved working files from:\n  {nodes_path}\n  {edges_path}")
            try:
                nodes = np.load(nodes_path)
                edges = np.load(edges_path)

                # Calculate basic D (Max Euclidean distance) from saved data
                if nodes.size > 0:
                    p2d = nodes[:, 1:3]  # x, y columns
                    # vectorized distance calculation
                    dists = np.sqrt(((p2d[:, None] - p2d[None, :]) ** 2).sum(axis=-1))
                    D = np.max(dists) if dists.size > 0 else 1.0

                    # Reconstruct file names based on unique lane IDs (col 4)
                    unique_lanes = np.unique(nodes[:, 4]).astype(int)
                    # We assume names are generic since original filenames aren't saved in the numpy array
                    file_names = [f"Edited Lane {i}" for i in unique_lanes]

                print(f"Loaded edited data: {len(nodes)} nodes.")
            except Exception as e:
                print(f"Error loading graph data: {e}")
                nodes = np.array([])
                edges = np.array([])
        else:
            print("No working files found (graph_nodes/edges).")

        self.D = D  # Update local D
        return nodes, edges, file_names, D

    def load_data(self, specific_files=None, start_id=0):
        """Load and process RAW .npy files from the specified directory.
        
        This function retrieves all .npy files from the directory specified by
        `self.directory` or uses a user-provided list of specific files. It processes
        each file to extract points, constructs nodes and edges, and performs data
        integrity checks, such as ensuring the presence of at least two columns in the
        data. The function maintains a unique point ID for each node and calculates the
        maximum distance between points if valid data is loaded.
        
        Args:
            self: The instance of the class containing the directory and file order attributes.
            specific_files (list?): A list of specific .npy files to load.
            start_id (int?): The starting ID for point identification.
        
        Returns:
            tuple: A tuple containing:
                - np.ndarray: An array of nodes.
                - np.ndarray: An array of edges.
                - list: A list of file names processed.
        """
        if specific_files:
            # Use the list provided by the user
            files = [f for f in specific_files if os.path.exists(os.path.join(self.directory, f))]
            if len(files) != len(specific_files):
                print("Warning: Some specified files were not found.")
        else:
            all_files = [f for f in os.listdir(self.directory) if f.endswith('.npy')]
            if not all_files:
                print(f"No .npy files found in directory: {self.directory}")
                return np.array([]), np.array([]), []

            if self.file_order:
                files = [f for f in self.file_order if f in all_files]
                files += [f for f in all_files if f not in files]
            else:
                files = sorted(all_files)

        nodes_list = []
        edges_list = []
        file_names = []

        # Initialize counter with the provided start_id
        point_id_counter = start_id

        for lane_idx, file in enumerate(files):
            file_path = os.path.join(self.directory, file)
            try:
                points = np.load(file_path)
                if points.size == 0:
                    continue

                if len(points.shape) == 1:
                    points = points.reshape(-1, points.shape[0])

                if points.shape[1] < 2:
                    continue

                N = points.shape[0]

                # Nodes: [point_id, x, y, yaw, original_lane_id]
                nodes = np.zeros((N, 5))
                edges = np.zeros((N - 1, 2), dtype=int)

                current_lane_point_ids = []

                nodes[:, 1:3] = points[:, 0:2]
                # Leave yaw (col 3) as 0.0 for now

                # Important: If we are appending, we might want to offset the lane_id too,
                nodes[:, 4] = lane_idx

                # Assign globally unique point_ids starting from start_id
                for i in range(N):
                    new_id = point_id_counter + i
                    nodes[i, 0] = new_id
                    current_lane_point_ids.append(new_id)

                for i in range(N - 1):
                    edges[i, 0] = current_lane_point_ids[i]
                    edges[i, 1] = current_lane_point_ids[i + 1]

                nodes_list.append(nodes)
                edges_list.append(edges)
                file_names.append(file)

                point_id_counter += N

            except Exception as e:
                print(f"Error loading file {file}: {e}")
                continue

        if not nodes_list:
            print("No valid data loaded")
            return np.array([]), np.array([]), []

        all_nodes = np.vstack(nodes_list)
        all_edges = np.vstack(edges_list)

        # Calculate D for raw data
        if all_nodes.size > 0:
            points_2d = all_nodes[:, 1:3]
            distances = np.sqrt(((points_2d[:, None] - points_2d[None, :]) ** 2).sum(axis=-1))
            current_D = np.max(distances) if distances.size > 0 else 1.0
            self.D = max(self.D, current_D)

        self.file_order = file_names
        print(f"Loaded {len(file_names)} raw files, total nodes: {all_nodes.shape[0]}")

        return all_nodes, all_edges, file_names
