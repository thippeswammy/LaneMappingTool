# Data Visualization and Editing Tool for Lane Data

## Overview
The **Data Visualization and Editing Tool** is a Python-based application designed for visualizing, editing, and managing lane data stored in NumPy (`.npy`) files. It provides an interactive Matplotlib interface for users to manipulate lane points, merge lanes, smooth segments, and draw new lanes, making it ideal for tasks like annotating road lanes for autonomous driving or mapping applications. The tool supports undo/redo operations, lane highlighting, and advanced navigation features to enhance usability and precision.

## Why It’s Used
This tool is used to:
- **Visualize Lane Data**: Display lane points (x, y coordinates with yaw, indices, and lane IDs) from `.npy` files in an interactive plot.
- **Edit Lane Data**: Add, delete, merge, or smooth lane points to correct or refine datasets.
- **Annotate New Lanes**: Draw new lanes as lines or smoothed curves for data augmentation.
- **Ensure Data Integrity**: Save edited data to `.npy` files with backup support to prevent data loss.
- **Support Autonomous Driving**: Refine lane annotations for path planning, mapping, or simulation in self-driving car development.

## Features
- **Interactive Visualization**: Plot lane points with unique colors per lane, start point markers, and a legend for navigation.
- **Point Editing**:
  - Add points by clicking in add/delete mode.
  - Delete points via right-click or selection + Delete key.
  - Change lane IDs for selected points.
- **Lane Drawing**: Draw new lanes as straight lines or smoothed curves, finalized with the Enter key.
- **Lane Merging**: Merge two lanes by selecting start/end points, with automatic yaw recalculation.
- **Segment Smoothing**: Smooth selected lane segments using spline interpolation, with preview and adjustable smoothness.
- **Undo/Redo**: Revert or reapply changes with `Ctrl+Z` and `Ctrl+Shift+Z` (or `Ctrl+Y`).
- **Lane Highlighting**: Click legend entries to highlight specific lanes with larger point sizes.
- **Tooltip**: Hover over points to display details (x, y, lane ID, index).
- **Zoom and Pan**: Scroll to zoom and drag to pan for precise navigation.
- **Export Selected Points**: Save selected points to a `.npy` file for further analysis.
- **Grid Toggle**: Enable/disable grid for better point alignment visualization.
- **Auto-Save Backup**: Periodically save backups to a `workspace-Backup` folder to prevent data loss.
- **Error Handling**: Robust error handling for file loading, smoothing, and plotting operations.
- **Status Messages**: Temporary status updates (e.g., "Point added") with a 5-second timeout.

### Workflow
- **Load Data**: The tool reads `.npy` files from a directory (e.g., `F:/RunningProjects/SAM2/lanes`).
- **Visualize**: Points are plotted with lane-specific colors, start points as squares, and a legend for interaction.
- **Edit**:
  - **Add/Delete Mode**: Click to add points, right-click to delete.
  - **Selection Mode**: Drag to select points, then smooth, delete, or export.
  - **Draw Mode**: Click to draw points, press Enter to finalize as a line or curve.
  - **Merge Mode**: Select start/end points of two lanes to merge them.
  - **Smooth Mode**: Select points, choose start/end, and apply spline smoothing.
- **Save**: Save all lanes to `workspace-Temp` or export selected points to `.npy` files.
- **Backup**: Auto-saves backups every 5 minutes to `workspace-Backup`.

### Prepare Data:
   - Place `.npy` files in a directory (e.g., `./lanes`).
   - Each file should contain an array of shape `(N, 2)` or `(N, 3)` for x, y, and optional yaw.

### Running the Tool

1. **Run the Application**:
   ```bash
   python main.py
   ```
   ```bash
   DataEditer.exe
   ```

2. **Interact with the Interface**:
   - **Modes**:
     - **Add/Delete**: Default mode; click to add points, right-click to delete.
     - **Selection**: Press `Tab` to enter; drag to select points.
     - **Draw**: Press `D` to enter; click to add points, `Enter` to finalize.
     - **Merge**: Click "Merge Lanes" button, select start/end points.
     - **Smooth**: In selection mode, select points, click "Smooth," choose start/end.
   - **Navigation**:
     - Scroll to zoom, drag to pan.
     - Hover for tooltips, click legend to highlight lanes.
   - **Shortcuts**:
     - `Ctrl+Z`: Undo.
     - `Ctrl+Shift+Z` or `Ctrl+Y`: Redo.
     - `Delete`: Delete selected points.
     - `Escape`: Reset to add/delete mode.
   - **Buttons**:
     - Toggle modes, save data, export selected points, toggle grid, etc.
   - **Save**: Click "Save" to save to `WorkingLane.npy`, or "Merge Lanes" to save to `workspace-Temp`.

## Directory Structure
```
DataVisualizationEditingTool/
├── lanes/                          # Input lane .npy files
│   └── lane_0.npy, lane_1.npy, ... # Individual lane files
│
├── utils/                          # Utility modules
│   ├── data_loader.py              # Loads and merges .npy lane files
│   ├── data_manager.py             # Manages lane data (add, delete, merge, save)
│   ├── event_handler.py            # Handles events (clicks, selections, modes)
│   ├── plot_manager.py             # Renders and updates Matplotlib plot and widgets
│   ├── curve_manager.py            # Manages lane drawing and smoothing logic
│   ├── network_.py                 # Launches network viewer, handles threading
│   └── network_view2.py            # Displays lane graph (network) view
│
├── workspace-Temp/                # Temporary saves (auto-generated at runtime)
├── workspace-Backup/              # Backup saves (auto-generated at runtime)
│
├── main.py                        #  Entry point: loads data, initializes GUI
├── DataEditer.exe                 # Compiled executable version (optional)
├── README.md                      #  Project overview and usage instructions

```