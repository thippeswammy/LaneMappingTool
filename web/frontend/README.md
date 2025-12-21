# Lane Mapping Tool - Frontend

This directory contains the React-based frontend for the Lane Mapping Tool. It provides an interactive interface for visualizing and editing lane graphs.

## 🔧 Setup

### Prerequisites

*   Node.js 16 or higher
*   npm (Node Package Manager)

### Installation

1.  Navigate to this directory:
    ```bash
    cd web/frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

## 🚀 Development

Start the development server:

```bash
npm run dev
```

The application will be accessible at `http://localhost:5173`. Ensure the backend server is running on port 5000.

## ⌨️ Keyboard Shortcuts

| Key                            | Action                        | Context          |
| :----------------------------- | :---------------------------- | :--------------- |
| **`d`**                        | switch to **Draw Mode**       | Global           |
| **`Esc`**                      | Cancel Draw / Clear Selection | Global           |
| **`Enter`**                    | Finalize Drawn Path           | Draw Mode        |
| **`Delete`** / **`Backspace`** | Delete Selected Nodes         | Selection Active |
| **`Ctrl + Z`**                 | Undo                          | Global           |
| **`Ctrl + Y`**                 | Redo                          | Global           |
| **`Shift + Click`**            | Multi-select Nodes            | Plot Area        |
| **`Ctrl + Click`**             | Add Node / Connect            | Plot Area        |
| **`Ctrl + Drag`**              | Brush/Box Select              | Box/Brush Mode   |

## 🎮 UI Guide

### Sidebar Modes
The sidebar has two main tabs:
*   **Edit:** Contains tools for manipulating the graph structure (Draw, Select, Connect, Smooth, Reverse).
*   **Config:** Contains tools for inspecting node properties and batch-updating attributes (Lane ID/Zone, Indicators).

### Visualization Controls
*   **Show Yaw:** Toggles the display of yaw direction arrows on nodes.
*   **Show Saved Layout:** Overlays the last saved graph state (blue dots/lines) for comparison.
*   **Point Size:** Slider in the bottom bar to adjust node visibility.

### Graph Operations
*   **Smooth Path:** Select a path (start & end nodes) and apply B-Spline smoothing. Adjust `Smoothness` and `Weight` sliders to control the curve.
*   **Connect Nodes:** Select two nodes to create a directed edge between them.
*   **Remove Between:** Select two nodes to delete all nodes in the shortest path between them.

## 📜 Scripts

*   `npm run dev`: Starts the development server.
*   `npm run build`: Builds the application for production.
*   `npm run lint`: Runs ESLint.

