import numpy as np
import matplotlib.pyplot as plt
import os

# ===== FILE PATH (GIVEN) =====
# Get the project root directory (parent of utils folder)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Construct the path dynamically
npy_file = os.path.join(project_root, "lanes", "new", "lane-03.npy")

# ===== LOAD & CHECK =====
if not os.path.exists(npy_file):
    raise FileNotFoundError(f"File not found: {npy_file}")

lane = np.load(npy_file)   # expected shape: (N, 3) -> x, y, yaw

# ===== VISUALIZATION =====
x = lane[:, 0]
y = lane[:, 1]

plt.figure()
plt.plot(x, y, marker='o')
plt.scatter(x[0], y[0], marker='s')      # start
plt.scatter(x[-1], y[-1], marker='x')    # end
plt.axis('equal')
plt.title("Lane Visualization: lane-0.npy")
plt.xlabel("X")
plt.ylabel("Y")
plt.show()
