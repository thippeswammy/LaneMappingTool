# Release v2.0.0

**Title:** v2.0.0 — Analysis module, improved smoothing, UI and data Format

## Overview
This major release introduces a suite of tools for in-depth data analysis, significantly improves the path smoothing algorithm to eliminate steering jerk, and enhances the user interface with real-time validation and better visualization features.

## 🚀 New Features

### Analysis & Data Integrity
- **Analysis Module**: New tools to compare lane data from original `.npy` files with processed `.pickle` outputs, ensuring data fidelity.
- **Path Direction Validation**: Real-time validation to check if node yaw aligns with the path direction, highlighting inconsistencies.
- **Improved Smoothing Algorithm**: The smoothing tool now correctly recalculates **Yaw (Heading)** along with X, Y coordinates, resolving steering jerk issues in autonomous tracking.

### User Interface Enhancements
- **Saved Graph Overlay**: Users can now toggle a visual overlay of the saved `output.json` graph (blue dots/dashed lines) directly on the plot to compare with the current edit state.
- **Enhanced Directory Browser**: Fixed path handling, added editable path input, and quick access buttons for drives (C:, D:, etc.).
- **Yaw Visualization**: Refined arrow rendering to accurately show vehicle heading, removing the misleading "acceptance cone".

### Operation & Workflow
- **"Force" Path Operations**: Added ability to force operations (Smooth, Reverse, Remove) on paths that may have minor discontinuities, with user confirmation.
- **State Management**: Improved frontend state handling to prevent operation conflicts (e.g., sticking in "Reverse" mode).

## 🐛 Bug Fixes
- **Node ID Collisions**: Fixed a critical issue where adding new points could duplicate existing Node IDs, corrupting the graph.
- **Operation Persistence**: Resolved bugs where previous operation states (start/end nodes) persisted incorrectly across different tools.
- **Yaw Calculation**: Fixed logic errors in `Plot.jsx` visualization that caused arrows to point in wrong directions under certain aspect ratios.

## 🛠️ Technical Improvements
- **Dependencies**: Updated `package.json` and backend requirements.
- **Code Structure**: Refactored `DataManager` to better handle ID synchronization.

## 📋 Deployment Workflow
**Steps to deploy the new map to the vehicle:**

1. **Save Data**:
   - Click the "Save Data" button in the web tool.
   - This creates `output.json` in `web/backend/workspace/`.

2. **Transfer Files**:
   - Copy `output.json` from your computer to the vehicle.
   - **Destination**: `AGC_ws/Network/` on the vehicle.

3. **Convert to Pickle (On Vehicle)**:
   - Ensure `json_to_pickle.py` is present in `AGC_ws/Network/`.
   - Run the conversion script using the vehicle's python (Python 2.7):
     ```bash
     python json_to_pickle.py output.json output.pickle
     ```
   - This generates the Python 2.6/2.7 and networkx compatible `.pickle` file required by the autonomous stack.

4. **Verify & Restart**:
   - Confirm `output.pickle` is created.