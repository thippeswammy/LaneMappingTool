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
        self.file_order = file_order  # custom order provided by user

    def load_data(self):
        all_files = [f for f in os.listdir(self.directory) if f.endswith('.npy')]
        if not all_files:
            print(f"No .npy files found in directory: {self.directory}")
            return np.array([]), []

        # If user gave a custom file order → respect it
        if self.file_order:
            files = [f for f in self.file_order if f in all_files]
            files += [f for f in all_files if f not in files]
        else:
            files = sorted(all_files)

        data_list = []
        file_names = []

        for lane_idx, file in enumerate(files):
            file_path = os.path.join(self.directory, file)
            try:
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
                data = np.zeros((N, 6))
                data[:, 0:2] = points[:, 0:2]

                if points.shape[1] >= 3:
                    data[:, 2] = points[:, 2]
                else:
                    for j in range(1, N):
                        dx = points[j, 0] - points[j - 1, 0]
                        dy = points[j, 1] - points[j - 1, 1]
                        data[j - 1, 2] = np.arctan2(dy, dx)

                if points.shape[1] >= 4:
                    data[:, 3] = points[:, 3]
                else:
                    data[:, 3] = np.arange(N)

                data[:, 4] = np.arange(N)       # index within file
                data[:, 5] = lane_idx           # lane index = order chosen

                data_list.append(data)
                file_names.append(file)
            except Exception as e:
                print(f"Error loading file {file}: {e}")
                continue

        if not data_list:
            print("No valid data loaded")
            return np.array([]), []

        merged_data = np.vstack(data_list)
        N_total = merged_data.shape[0]
        merged_data[:, 3] = np.arange(N_total)
        merged_data[:, 4] = np.arange(N_total)

        # compute max distance for scaling
        if merged_data.size > 0:
            points_2d = merged_data[:, :2]
            distances = np.sqrt(((points_2d[:, None] - points_2d[None, :]) ** 2).sum(axis=-1))
            self.D = np.max(distances) if distances.size > 0 else 1.0
        else:
            self.D = 1.0

        self.file_order = file_names  # store final order used
        print(f"Loaded {len(file_names)} files, total points: {N_total}")
        return merged_data, file_names
