import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Tuple
import numpy as np

# Add the project root to sys.path to allow imports from DataVisualizationEditingTool
# Assuming this file is in DataVisualizationEditingTool/web/backend/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from DataVisualizationEditingTool.utils.data_loader import DataLoader
from DataVisualizationEditingTool.utils.data_manager import DataManager

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
class AppState:
    def __init__(self):
        self.data_manager: Optional[DataManager] = None
        self.D = 1.0

state = AppState()

# Pydantic Models
class NodeData(BaseModel):
    id: int
    x: float
    y: float
    yaw: float
    lane_id: int

class EdgeData(BaseModel):
    from_id: int
    to_id: int

class InitResponse(BaseModel):
    nodes: List[NodeData]
    edges: List[EdgeData]
    file_names: List[str]
    D: float

class AddNodeRequest(BaseModel):
    x: float
    y: float
    lane_id: int

class AddEdgeRequest(BaseModel):
    from_id: int
    to_id: int

class DeleteRequest(BaseModel):
    point_ids: List[int]

@app.get("/api/init", response_model=InitResponse)
def init_data():
    base_path = os.path.abspath(os.path.join(current_dir, "../../"))
    files_dir = os.path.join(base_path, 'files')
    original_data_path = os.path.join(base_path, 'originalData')

    # Ensure directories exist
    os.makedirs(files_dir, exist_ok=True)
    
    # These files must exist in your 'original_data_path' folder
    # Matching main.py logic
    files_path_ = ["lane-3.npy"] 
    
    nodes_path = os.path.join(files_dir, 'WorkingNodes1.npy')
    edges_path = os.path.join(files_dir, 'WorkingEdges1.npy')
    files_path = [os.path.join(original_data_path, i) for i in files_path_]
    
    final_nodes = np.array([])
    final_edges = np.array([])
    file_names = []
    D = 1.0

    # Load Saved Working Data
    if os.path.exists(nodes_path) and os.path.exists(edges_path):
        print("Loading saved working files...")
        saved_nodes = np.load(nodes_path)
        saved_edges = np.load(edges_path)

        if saved_nodes.size > 0:
            p2d = saved_nodes[:, 1:3]
            dists = np.sqrt(((p2d[:, None] - p2d[None, :]) ** 2).sum(axis=-1))
            D = np.max(dists) if dists.size > 0 else 1.0
            unique_lanes = np.unique(saved_nodes[:, 4]).astype(int)
            file_names = [f"Edited Lane {i}" for i in unique_lanes]

        final_nodes = saved_nodes
        final_edges = saved_edges
    else:
        print("No working files found. Starting clean.")

    # Load new Raw Data and Merge
    if files_path:
        print(f"Attempting to merge {len(files_path)} new raw files...")
        loader = DataLoader(original_data_path)
        
        start_id_offset = 0
        lane_id_offset = 0

        if final_nodes.size > 0:
            start_id_offset = int(np.max(final_nodes[:, 0])) + 1
            lane_id_offset = int(np.max(final_nodes[:, 4])) + 1

        try:
            new_nodes, new_edges, new_names = loader.load_data(
                specific_files=files_path,
                start_id=start_id_offset
            )

            if new_nodes.size > 0:
                new_nodes[:, 4] += lane_id_offset
                if final_nodes.size > 0:
                    final_nodes = np.vstack([final_nodes, new_nodes])
                    final_edges = np.vstack([final_edges, new_edges])
                    file_names.extend(new_names)
                    D = max(D, loader.D)
                else:
                    final_nodes = new_nodes
                    final_edges = new_edges
                    file_names = new_names
                    D = loader.D
        except Exception as e:
            print(f"Error loading new files: {e}")

    # Initialize DataManager
    state.data_manager = DataManager(final_nodes, final_edges, file_names)
    state.D = D

    return _get_state_response()

def _get_state_response():
    if state.data_manager is None:
        return {"nodes": [], "edges": [], "file_names": [], "D": 1.0}
    
    nodes = []
    if state.data_manager.nodes.size > 0:
        for n in state.data_manager.nodes:
            nodes.append(NodeData(id=int(n[0]), x=float(n[1]), y=float(n[2]), yaw=float(n[3]), lane_id=int(n[4])))
            
    edges = []
    if state.data_manager.edges.size > 0:
        for e in state.data_manager.edges:
            edges.append(EdgeData(from_id=int(e[0]), to_id=int(e[1])))
            
    return {
        "nodes": nodes,
        "edges": edges,
        "file_names": state.data_manager.file_names,
        "D": state.D
    }

@app.get("/api/state")
def get_state():
    if state.data_manager is None:
        # Try to init if not initialized
        return init_data()
    return _get_state_response()

@app.post("/api/action/add_node")
def add_node(req: AddNodeRequest):
    if state.data_manager is None: raise HTTPException(status_code=400, detail="Not initialized")
    new_id = state.data_manager.add_node(req.x, req.y, req.lane_id)
    if new_id is None:
        raise HTTPException(status_code=500, detail="Failed to add node")
    return _get_state_response()

@app.post("/api/action/add_edge")
def add_edge(req: AddEdgeRequest):
    if state.data_manager is None: raise HTTPException(status_code=400, detail="Not initialized")
    state.data_manager.add_edge(req.from_id, req.to_id)
    return _get_state_response()

@app.post("/api/action/delete")
def delete_points(req: DeleteRequest):
    if state.data_manager is None: raise HTTPException(status_code=400, detail="Not initialized")
    state.data_manager.delete_points(req.point_ids)
    return _get_state_response()

@app.post("/api/action/undo")
def undo():
    if state.data_manager is None: raise HTTPException(status_code=400, detail="Not initialized")
    state.data_manager.undo()
    return _get_state_response()

@app.post("/api/action/redo")
def redo():
    if state.data_manager is None: raise HTTPException(status_code=400, detail="Not initialized")
    state.data_manager.redo()
    return _get_state_response()

@app.post("/api/save")
def save():
    if state.data_manager is None: raise HTTPException(status_code=400, detail="Not initialized")
    path = state.data_manager.save()
    if path:
        return {"status": "success", "path": path}
    else:
        raise HTTPException(status_code=500, detail="Save failed")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
