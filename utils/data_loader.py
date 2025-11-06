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

    def load_data(self):
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

        point_id_counter = 0

        for lane_idx, file in enumerate(files):
            file_path = os.path.join(self.directory, file)
            try:
                points = np.load(file_path)
                if points.size == 0:
                    print(f"Empty file: {file}")
                    continue

                if len(points.shape) == 1:
                    points = points.reshape(-1, points.shape[0])

                # --- MODIFICATION ---
                # We now only require 2 columns (x, y).
                # The error was caused by trying to access columns that don't exist.
                if points.shape[1] < 2:
                    print(f"File {file} must have at least 2 columns (x, y), got shape {points.shape}")
                    continue
                # --- END MODIFICATION ---

                N = points.shape[0]

                # Nodes: [point_id, x, y, yaw, original_lane_id]
                # By initializing with zeros, yaw (index 3) is already 0.0
                nodes = np.zeros((N, 5))
                edges = np.zeros((N - 1, 2), dtype=int)

                current_lane_point_ids = []

                # --- Populate Nodes ---
                # We only read columns 0 and 1 (x, y)
                nodes[:, 1:3] = points[:, 0:2]

                # --- YAW LOADING REMOVED ---
                # As requested ("keep the 3 axit to zero"), we will
                # leave nodes[:, 3] (yaw) as 0.0.
                # We are no longer accessing points[:, 2] or points[:, 3].
                # --- END REMOVAL ---

                nodes[:, 4] = lane_idx  # original_lane_id

                # Assign globally unique point_ids
                for i in range(N):
                    new_id = point_id_counter + i
                    nodes[i, 0] = new_id
                    current_lane_point_ids.append(new_id)

                # --- Populate Edges ---
                # Create the sequential connections for this lane
                for i in range(N - 1):
                    edges[i, 0] = current_lane_point_ids[i]  # from_id
                    edges[i, 1] = current_lane_point_ids[i + 1]  # to_id

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

        if all_nodes.size > 0:
            points_2d = all_nodes[:, 1:3]  # x, y columns
            distances = np.sqrt(((points_2d[:, None] - points_2d[None, :]) ** 2).sum(axis=-1))
            self.D = np.max(distances) if distances.size > 0 else 1.0
        else:
            self.D = 1.0

        self.file_order = file_names
        print(f"Loaded {len(file_names)} files, total nodes: {all_nodes.shape[0]}, total edges: {all_edges.shape[0]}")

        return all_nodes, all_edges, file_names