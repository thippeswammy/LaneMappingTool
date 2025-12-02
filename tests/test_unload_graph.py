import pytest
import numpy as np
from web.backend.app import app, data_manager

@pytest.fixture
def client():
    """Create a test client for the application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_unload_graph(client):
    # 1. Setup: Load some mixed data
    # Raw data (simulated)
    """Test the /api/unload_graph endpoint."""
    data_manager.nodes = np.array([[0, 0, 0, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1]])
    data_manager.edges = np.array([[0, 1]])
    data_manager.file_names = ['lane-01.npy', 'Edited Lane 0']
    
    # Verify setup
    assert len(data_manager.file_names) == 2
    
    # 2. Call unload_graph endpoint
    response = client.post('/api/unload_graph')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    
    # 3. Verify only "Edited Lane" files are removed
    # Note: remove_file sets the entry to None to preserve indices
    assert 'lane-01.npy' in data_manager.file_names
    assert 'Edited Lane 0' not in data_manager.file_names
    assert data_manager.file_names[1] is None
    
    # Verify response contains filtered list
    assert len(data['file_names']) == 1
    assert 'lane-01.npy' in data['file_names']
    assert 'Edited Lane 0' not in data['file_names']
    
    # Note: The actual node/edge removal logic in DataManager depends on how remove_file is implemented.
    # Assuming remove_file correctly filters nodes/edges based on the file index.
    # Since we mocked the data manually without setting up the internal mapping in DataManager (which might be complex),
    # we primarily test that the file name is removed and the endpoint returns success.
    # For a full integration test, we would need to load actual files.
