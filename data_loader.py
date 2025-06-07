import os

import numpy as np


class DataLoader:
    def __init__(self, directory):
        self.directory = directory
        self.D = None  # Will be computed in load_data

    def load_data(self):
        # List all .npy files in the directory
        files = [f for f in os.listdir(self.directory) if f.endswith('.npy')]
        if not files:
            print(f"No .npy files found in directory: {self.directory}")
            return np.array([]), []

        # Load each file and assign a file index (lane ID)
        data_list = []
        file_names = []
        for idx, file in enumerate(files):
            file_path = os.path.join(self.directory, file)
            points = np.load(file_path)
            if points.size == 0:
                continue
            # print('points=>', points[0:2], 'len', len(points))
            # pointss = []
            # for i, n in enumerate(points):
            #     print(i, n)
            #     # pointss.append()
            # points.appends()
            # Ensure the last column is the lane ID
            points[:, -1] = idx  # Overwrite the last column with the lane ID
            data_list.append(points)
            file_names.append(file)

        # Merge all data
        if not data_list:
            merged_data = np.array([])
        else:
            merged_data = np.vstack(data_list)

        # Compute D (maximum distance between points in x-y space)
        if merged_data.size > 0:
            points_2d = merged_data[:, :2]
            distances = np.sqrt(((points_2d[:, None] - points_2d[None, :]) ** 2).sum(axis=-1))
            self.D = np.max(distances) if distances.size > 0 else 1.0
        else:
            self.D = 1.0  # Default value if no data
        return merged_data, file_names
