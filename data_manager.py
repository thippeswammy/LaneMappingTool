import numpy as np
from datetime import datetime


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
        if indices:
            self.undo_stack.append(('delete', self.data[indices].copy(), indices))
            self.redo_stack.clear()
            self.data = np.delete(self.data, indices, axis=0)
        return self.data

    def change_ids(self, indices, new_id):
        if indices:
            self.undo_stack.append(('change_id', self.data[indices].copy(), indices))
            self.redo_stack.clear()
            self.data[indices, self.D] = new_id
        return self.data

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
        if not self.redo_stack:
            return self.data, False
        action, data, *rest = self.redo_stack.pop()
        if action == 'add':
            self.undo_stack.append(('add', data))
            self.data = np.vstack((self.data, data)) if self.data.size else data
        elif action == 'delete':
            indices = rest[0]
            self.undo_stack.append(('delete', self.data[indices].copy(), indices))
            self.data = np.delete(self.data, indices, axis=0)
        elif action == 'change_id':
            indices = rest[0]
            self.undo_stack.append(('change_id', self.data[indices].copy(), indices))
            self.data[indices] = data
        return self.data, True

    def save(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'merged_edited_{timestamp}.npy'
        np.save(filename, self.data)
        return filename