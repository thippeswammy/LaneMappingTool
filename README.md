# Lane Mapping & Visualization Tool

A Python-based GUI tool designed for visualizing, editing, and refining lane graph data for autonomous vehicle navigation. This tool allows for the creation of directed graphs from raw waypoint data (`.npy`), enabling complex operations like path smoothing, connection management, and direction reversal.

## 🚀 Features

* **Graph-Based Data Model:** Treats lanes as nodes and edges, supporting complex junctions (Y-splits, merges) rather than just linear lists.
* **Bidirectional Editing:** Algorithms for smoothing and pathfinding work in both forward and reverse directions.
* **Advanced Curve Smoothing:** Uses B-Spline interpolation (`scipy.interpolate`) to smooth jagged paths between selected nodes with adjustable weight and smoothness factors.
* **Path Management:**
    * **Connect Nodes:** Link disjointed paths or create loops.
    * **Remove Between:** Automatically find the path between two nodes and delete all intermediate points.
    * **Reverse Path:** Intelligent pathfinding to reverse the direction of edges along a selected route.
* **NetworkX Integration:** Exports the final graph as a NetworkX `.pickle` file with attributes (`id`,`x`, `y`, `yaw`, `original_lane_id`) -> (`id`,`x`, `y`, `yaw`, `zone`,`width`, `indicator`) suitable for autonomous navigation stacks.
* **Session Resume:** Automatically detects and loads saved working files (`WorkingNodes.npy`) to resume editing sessions.

## 🛠️ Installation

Ensure you have Python installed. Install the required dependencies:

```bash
pip install numpy matplotlib networkx scipy
````

## 📂 Project Structure

```text
LaneMappingTool
├── originalData/          # Place raw lane-X.npy files here
├── files/                 # Output location for saved WorkingNodes/Edges and output.pickle
├── utils/
│   ├── data_loader.py     # Loads raw .npy files
│   ├── data_manager.py    # Manages the Node/Edge graph structure
│   ├── event_handler.py   # Handles mouse/keyboard inputs and state machine
│   ├── plot_manager.py    # Matplotlib plotting logic
│   └── curve_manager.py   # B-Spline smoothing and pathfinding algorithms
├── main.py                # Entry point for the application
└── network_view3.py       # Viewer script to validate the exported pickle graph
```

## 🎮 Controls & Usage

### Basic Interaction

| Action | Control | Description |
| :--- | :--- | :--- |
| **Select Node** | `Left Click` | Highlights a single node. |
| **Add Node** | `Ctrl` + `Left Click` | Adds a new node at the cursor location, connected to the previously selected node. |
| **Delete Node** | `Right Click` | Deletes the clicked node and its connections. |
| **Break Connection**| `Ctrl` + `Right Click`| Deletes all **incoming** edges to the clicked node (breaks the path). |
| **Area Select** | `Ctrl` + `S` + `Drag` | Selects multiple nodes within a rectangle. |
| **Pan/Zoom** | Mouse Wheel / Drag | Standard Matplotlib navigation. |

### Editing Modes (Buttons)

  * **Draw:** Click repeatedly to sketch a new lane. Press `Enter` to finalize and commit the lane to the graph.
  * **Smooth:**
    1.  Click **"Smooth"**.
    2.  Click the **Start Node**.
    3.  Click the **End Node**.
    4.  Adjust the **Smoothness** and **Weight** sliders to see a real-time blue preview line.
    5.  Click **"Confirm Smooth"** to apply changes.
  * **Connect Nodes:** Select two disjoint nodes to create a directed edge between them.
  * **Remove Between:** Select a Start and End node. The tool finds the path between them and deletes all intermediate nodes.
  * **Reverse Path:** Select a Start and End node. The tool reverses the direction of all edges along that path.

## 💾 Data Output

When you click **Save**, the tool generates three files in the `files/` directory:

1.  **`WorkingNodes.npy`**: Numpy array containing `[point_id, x, y, yaw, original_lane_id]`. Used to resume editing. # Need to fix
2.  **`WorkingEdges.npy`**: Numpy array containing `[from_id, to_id]`. Used to resume editing.
3.  **`output.pickle`**: A serialized `networkx.DiGraph` object.
      * **Nodes:** Contain attributes `x`, `y`, `yaw`, `zone=0`, `width=0`, `indicator=0`. -> Need to fix
      * **Edges:** Contain `weight` calculated as the Euclidean distance.

## 📝 Author

**Thippeswamy K.S.**
*GITAM Deemed to be University, Bengaluru*
