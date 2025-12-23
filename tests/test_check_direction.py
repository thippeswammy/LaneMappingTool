
import pytest
import numpy as np
import sys
import os
import json
from flask import Flask

# Adjust path to import from the parent project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web.backend.app import app, data_manager

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_check_path_direction(client):
    # Setup Data
    # Path: 0 -> 1 -> 2
    # 0 at (0,0), 1 at (10,0), 2 at (20,0)
    # Direction is East (0 radians)
    
    # Node 0: Yaw 0 (Correct)
    # Node 1: Yaw PI/2 (Incorrect - 90 degrees mismatched)
    # Node 2: Yaw 0 (End node, yaw doesn't matter for path segment leaving 2, but matters if it continues. our logic checks i and i+1)
    
    nodes = np.array([
        [0, 0.0, 0.0, 0.0, 0, 3.0, 1],
        [1, 10.0, 0.0, 1.57, 0, 3.0, 1], # 90 deg yaw (approx 1.57 rad)
        [2, 20.0, 0.0, 0.0, 0, 3.0, 1]
    ])
    
    edges = np.array([
        [0, 1],
        [1, 2]
    ])
    
    data_manager.nodes = nodes
    data_manager.edges = edges
    data_manager.file_names = ["test_file"]
    
    # Test Request
    response = client.post('/api/check_path_direction', json={
        'start_id': 0,
        'end_id': 2,
        'threshold_deg': 45.0
    })
    
    assert response.status_code == 200
    data = response.json
    assert data['status'] == 'success'
    
    details = data['details']
    assert len(details) == 2 # 0->1, 1->2
    
    # Segment 0->1
    # Node 0 Yaw: 0. Path Dir: 0. Diff: 0. Status: ok.
    assert details[0]['id'] == 0
    assert details[0]['status'] == 'ok'
    
    # Segment 1->2
    # Node 1 Yaw: 1.57 (90 deg). Path Dir: 0. Diff: 90. Status: mismatch.
    assert details[1]['id'] == 1
    assert details[1]['status'] == 'mismatch'
    
    assert "found 1 mismatches" in data['overall_status'].lower()
    
    print("Test Validated: Successfully detected mismatch.")

if __name__ == "__main__":
    # Manually run if executed as script
    # Mocking client for manual run without pytest
    app.config['TESTING'] = True
    with app.test_client() as c:
        test_check_path_direction(c)
