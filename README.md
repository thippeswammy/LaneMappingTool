# Lane Mapping & Visualization Tool

A comprehensive tool for visualizing, editing, and refining lane graph data for autonomous vehicle navigation. This project has evolved from a desktop Python GUI to a modern Web Application with a React frontend and a Flask backend.

## 🚀 Features

*   **Web-Based Interface:** Modern, responsive UI built with React and Vite.
*   **Graph-Based Data Model:** Treats lanes as nodes and edges, supporting complex junctions.
*   **Bidirectional Editing:** Algorithms for smoothing and pathfinding work in both forward and reverse directions.
*   **Advanced Curve Smoothing:** B-Spline interpolation for smooth path generation.
*   **Interactive Plotting:** D3.js-like interactivity using Recharts/Visx (or similar) on the frontend, backed by Matplotlib logic on the backend.
*   **Session Persistence:** Automatically saves and loads working sessions.

## 🛠️ Quick Start

### Prerequisites

*   **Python 3.8+**
*   **Node.js 16+**

### 1. Backend Setup

Navigate to the backend directory and install dependencies:

```bash
cd web/backend
# Create a virtual environment (optional but recommended)
python -m venv venv
# Activate venv:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

Start the Flask server:

```bash
python app.py
```
The backend will run on `http://localhost:5000`.

### 2. Frontend Setup

Open a new terminal, navigate to the frontend directory, and install dependencies:

```bash
cd web/frontend
npm install
```

Start the development server:

```bash
npm run dev
```
The application will be accessible at `http://localhost:5173` (or the port shown in the terminal).

## 📂 Project Structure

```text
LaneMappingTool
├── web/
│   ├── backend/           # Flask API & Python logic
│   │   ├── app.py         # Main entry point
│   │   ├── utils/         # Core logic (data, plotting, curves)
│   │   └── ...
│   └── frontend/          # React Application
│       ├── src/           # Components & State
│       └── ...
├── originalData/          # Raw .npy files
├── files/                 # Output files
└── ...
```

## 🎮 Controls

*   **Left Click:** Select Node
*   **Ctrl + Left Click:** Add Node / Connect to existing
*   **Right Click:** Delete Node
*   **Ctrl + Right Click:** Break Connection
*   **Ctrl + Drag:** Multi-select (Brush/Box)
*   **Scroll:** Zoom
*   **Drag:** Pan

## 📝 Author

**Thippeswamy K.S.**
*GITAM Deemed to be University, Bengaluru*
