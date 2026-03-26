
import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Adjust path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.curve_manager import CurveManager
from utils.data_manager import DataManager

# Mocks
class MockPlotManager:
    class MockSlider:
        val = 0.5
    
    def __init__(self):
        self.slider_smooth = self.MockSlider()
        self.ax = plt.gca()
        self.fig = plt.gcf()
        self.selected_indices = []
    
    def update_plot(self, *args, **kwargs):
        """Update the plot with the given arguments."""
        """Update the plot with the given arguments."""
        pass

class MockEventHandler:
    def __init__(self):
        self.smoothing_path_ids = []
        self.smoothing_preview_line = None
        self.status = ""

    def update_status(self, msg):
        self.status = msg
        print(f"Status: {msg}")

def test_smoothing():
    """Test the smoothing logic for a set of nodes.
    
    This function sets up a DataManager with a linear path and creates  nodes at
    regular intervals. It then defines a selection of nodes to  smooth and
    resample, applying the smoothing logic through a  CurveManager. The function
    checks the results by verifying the  new node count and the average spacing of
    the smoothed path,  ensuring that the spacing is close to the target and that
    the  node count has increased.
    """
    print("--- Test: Smoothing Logic (Context + Resample) ---")
    
    # 1. Setup DataManager with a linear path
    dm = DataManager(np.empty((0, 4)), np.empty((0, 2)), [])
    
    # Create 10 points in a line (0,0) to (18,0) -> 2m spacing originally
    # p0(0,0), p1(2,0), p2(4,0) ...
    # We will select a middle segment to smooth and resample to 0.5m spacing.
    
    ids = []
    for i in range(10):
        pid = dm.add_node(i * 2.0, 0.0, original_lane_id=1)
        ids.append(pid)
        if i > 0:
            dm.add_edge(ids[i-1], pid)

    print(f"Original Nodes: {len(dm.nodes)}")
    
    # 2. Setup CurveManager
    pm = MockPlotManager()
    eh = MockEventHandler()
    cm = CurveManager(dm, pm, eh)
    
    # 3. Define Selection: p3 to p6 (6.0m to 12.0m)
    # Context should be p0,p1,p2 (left) and p7,p8,p9 (right)
    selection = ids[3:7] # [p3, p4, p5, p6]
    eh.smoothing_path_ids = selection
    
    start_mask = dm.nodes[:, 0] == selection[0]
    end_mask = dm.nodes[:, 0] == selection[-1]
    start_x = dm.nodes[start_mask][0][1]
    end_x = dm.nodes[end_mask][0][1]
    
    print(f"Selection: {selection} from x={start_x} to x={end_x}")
    print(f"Selection Length: {len(selection)} nodes")
    print(f"Expected Distance: {end_x - start_x} meters")
    
    # 4. Apply Smooth
    # Expected: 
    # - Resampling to ~0.5m spacing -> (12.0 - 6.0) / 0.5 = 12 segments -> ~13 points
    # - Original count is 4. New count should be significantly higher.
    
    cm.apply_smooth()
    
    # 5. Check Results
    # Count total nodes now
    # Original 10. Removed 2 intermediates (p4, p5). Added ~11 intermediates.
    
    new_nodes_count = len(dm.nodes)
    print(f"New Node Count: {new_nodes_count}")
    
    # Verify spacing of the new segment
    # Get neighbors of p3 (start of selection, id might be same)
    # Traverse from p3 to p6
    
    path = cm._find_path(selection[0], selection[-1])
    print(f"New Path IDs: {path}")
    print(f"New Path Length: {len(path)}")
    
    # Calculate spacing
    coords = []
    for pid in path:
        n = dm.nodes[dm.nodes[:, 0] == pid]
        coords.append(n[0, 1:3])
    coords = np.array(coords)
    
    dists = np.sqrt(np.sum(np.diff(coords, axis=0)**2, axis=1))
    avg_spacing = np.mean(dists)
    print(f"Average Spacing: {avg_spacing:.4f} m (Target 0.5)")
    
    if 0.4 < avg_spacing < 0.6:
        print("PASS: Spacing is uniform and close to target.")
    else:
        print("FAIL: Spacing incorrect.")
        
    if len(path) > len(selection):
        print("PASS: Node count increased (upsampled).")
    else:
        print("FAIL: Node count did not increase.")

if __name__ == "__main__":
    try:
        test_smoothing()
    except Exception as e:
        print(f"Test Failed with error: {e}")
        import traceback
        traceback.print_exc() 
