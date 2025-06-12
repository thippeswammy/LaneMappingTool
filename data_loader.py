import os
import numpy as np

class DataLoader:
    def __init__(self, directory):
        self.directory = directory
        self.D = None

    def load_data(self):
        files = [f for f in os.listdir(self.directory) if f.endswith('.npy')]
        if not files:
            print(f"No .npy files found in directory: {self.directory}")
            return np.array([]), []

        data_list = []
        file_names = []

        for i, file in enumerate(files):
            file_path = os.path.join(self.directory, file)
            points = np.load(file_path)
            if points.size == 0:
                print(f"Empty file: {file}")
                continue

            if len(points.shape) == 1:
                points = points.reshape(-1, points.shape[0])

            if points.shape[1] < 2:
                print(f"File {file} must have at least 2 columns (x, y), got shape {points.shape}")
                continue

            N = points.shape[0]
            # Add yaw if missing
            if points.shape[1] < 3:
                yaw = np.zeros((N, 1))
                for j in range(1, N):
                    dx = points[j, 0] - points[j-1, 0]
                    dy = points[j, 1] - points[j-1, 1]
                    yaw[j-1] = np.arctan2(dy, dx)
                points = np.hstack([points, yaw])

            # Add frame_idx and index (temporary per file)
            indices = np.arange(N).reshape(-1, 1)  # Used for both frame_idx and index

            # Add lane_id
            lane_ids = np.full((N, 1), i, dtype=int)

            # Combine: x, y, yaw, ..., frame_idx, index, lane_id
            merged_points = np.hstack([points, indices, indices, lane_ids])
            data_list.append(merged_points)
            file_names.append(file)

        if not data_list:
            print("No valid data loaded")
            return np.array([]), []

        merged_data = np.vstack(data_list)

        # Reassign global frame_idx and index
        N_total = merged_data.shape[0]
        merged_data[:, 3] = np.arange(N_total)  # frame_idx
        merged_data[:, -2] = np.arange(N_total)  # index

        # Compute D
        if merged_data.size > 0:
            points_2d = merged_data[:, :2]
            distances = np.sqrt(((points_2d[:, None] - points_2d[None, :]) ** 2).sum(axis=-1))
            self.D = np.max(distances) if distances.size > 0 else 1.0
        else:
            self.D = 1.0

        print(f"Loaded {len(file_names)} files, total points: {N_total}")
        if merged_data.size > 0:
            print(f"Sample merged_data:\n{merged_data[:5]}")
            print(f"Unique lane IDs: {np.unique(merged_data[:, -1])}")

        return merged_data, file_names