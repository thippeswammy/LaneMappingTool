import numpy as np
import matplotlib.pyplot as plt
import os

# ===== FILE PATH (GIVEN) =====
npy_file = r"/media/thippe/Thippeswamy/RunningProjects/LaneMappingTool/lanes/new/lane-03.npy"

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
