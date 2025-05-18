import numpy as np
import glob
import os
from data_loader import DataLoader

class DataManager:
    def __init__(self, data, file_names, D):
        self.data = data
        self.file_names = file_names
        self.D = D
        self.total_cols = D + 1 if D is not None else 3
        self.undo_stack = []
        self.redo_stack = []

    def add_point(self, x, y, file_id):
        new_point = np.zeros((1, self.total_cols))
        new_point[0, 0] = x
        new_point[0, 1] = y
        new_point[0, self.D] = file_id
        self.undo_stack.append(('add', new_point))
        self.redo_stack.clear()
        if self.data.size == 0:
            self.data = new_point
        else:
            self.data = np.vstack((self.data, new_point))
        return self.data

    def delete_points(self, indices):
        """Delete points at the specified indices."""
        if not indices:
            return
        mask = np.ones(len(self.data), dtype=bool)
        mask[indices] = False
        self.data = self.data[mask]
        # Don't save to history here; wait for the action to complete

    def change_ids(self, indices, new_file_id):
        """Change the file_id of points at the specified indices."""
        self.data[indices, self.D] = new_file_id
        # Don't save to history here; wait for the action to complete

    def undo(self):
        if not self.undo_stack:
            return self.data, False
        action, data, *rest = self.undo_stack.pop()
        if action == 'add':
            self.redo_stack.append(('add', data))
            self.data = self.data[:-1] if self.data.shape[0] > 1 else np.empty((0, self.total_cols))
        elif action == 'delete':
            indices = rest[0]
            self.redo_stack.append(('delete', data, indices))
            self.data = np.insert(self.data, indices, data, axis=0)
        elif action == 'change_id':
            indices = rest[0]
            self.redo_stack.append(('change_id', self.data[indices].copy(), indices))
            self.data[indices] = data
        return self.data, True

    def redo(self):
        """Redo the last undone action."""
        if self.action_in_progress:
            print("Cannot redo while an action is in progress.")
            return self.data, False
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.data = self.history[self.history_index][0].copy()
            print(f"Redone action: {self.history[self.history_index][1]}")
            return self.data, True
        print("Nothing to redo.")
        return self.data, False

    def save(self):
        """Save the current data to files."""
        output_dir = "output_lanes"
        os.makedirs(output_dir, exist_ok=True)
        for file_id in np.unique(self.data[:, self.D]):
            mask = self.data[:, self.D] == file_id
            points = self.data[mask, :2]
            filename = os.path.join(output_dir, f"lane-{int(file_id)}.npy")
            np.save(filename, points)
        return output_dir