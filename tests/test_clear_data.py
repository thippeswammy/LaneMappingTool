import pytest
import numpy as np
import os
from web.backend.app import app, data_manager

@pytest.fixture
def client():
    """Create a test client for the application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_clear_data(client):
    """Test the /api/clear endpoint."""
    # 1. Load some dummy data first
    data_manager.nodes = np.array([[0, 0, 0, 0, 0, 0, 0]])
    data_manager.edges = np.array([])
    data_manager.file_names = ['dummy.npy']
    
    # Verify data exists
    response = client.get('/api/data')
    data = response.get_json()
    assert len(data['nodes']) == 1
    
    # 2. Call clear endpoint
    response = client.post('/api/clear')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['nodes']) == 0
    assert len(data['edges']) == 0
    assert len(data['file_names']) == 0
    
    # 3. Verify backend state is cleared
    assert data_manager.nodes.size == 0
    assert data_manager.edges.size == 0
    assert len(data_manager.file_names) == 0
