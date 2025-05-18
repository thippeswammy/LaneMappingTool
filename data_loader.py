import glob

import numpy as np


class DataLoader:
    @staticmethod
    def load_and_merge_npy_files(file_pattern="../lanes/lane-*.npy"):
        files = glob.glob(file_pattern)
        all_data = []
        D = None
        for i, file in enumerate(files):
            data = np.load(file)
            if D is None:
                D = data.shape[1]
            elif data.shape[1] != D:
                raise ValueError(f"Inconsistent columns in {file}: expected {D}, got {data.shape[1]}")
            id_column = np.full((data.shape[0], 1), i)
            data_with_id = np.hstack((data, id_column))
            all_data.append(data_with_id)
        if all_data:
            merged_data = np.vstack(all_data)
        else:
            merged_data = np.empty((0, 3))
            D = 2
        return merged_data, files, D
