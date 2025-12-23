import requests
import json
import unittest
import time

BASE_URL = "http://127.0.0.1:5001"

class TestBackendOperations(unittest.TestCase):
    def setUp(self):
        # Clear data before each test
        requests.post(f"{BASE_URL}/api/unload_graph")
        time.sleep(0.1)

    def test_add_node_and_edge(self):
        # 1. Add Node A
        res = requests.post(f"{BASE_URL}/api/operation", json={
            "operation": "add_node",
            "params": {"x": 0, "y": 0, "lane_id": 0}
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        nodes = data['nodes']
        self.assertEqual(len(nodes), 1)
        node_a_id = nodes[0][0]

        # 2. Add Node B
        res = requests.post(f"{BASE_URL}/api/operation", json={
            "operation": "add_node",
            "params": {"x": 10, "y": 10, "lane_id": 0}
        })
        nodes = res.json()['nodes']
        node_b_id = nodes[1][0]

        # 3. Connect A -> B
        res = requests.post(f"{BASE_URL}/api/operation", json={
            "operation": "add_edge",
            "params": {"from_id": node_a_id, "to_id": node_b_id}
        })
        self.assertEqual(res.status_code, 200)
        edges = res.json()['edges']
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0][0], node_a_id)
        self.assertEqual(edges[0][1], node_b_id)

    def test_find_path(self):
        # Create A->B->C
        res = requests.post(f"{BASE_URL}/api/operation", json={"operation": "add_node", "params": {"x":0,"y":0,"lane_id":0}})
        id_a = res.json()['nodes'][0][0]
        res = requests.post(f"{BASE_URL}/api/operation", json={"operation": "add_node", "params": {"x":10,"y":0,"lane_id":0, "connect_to": id_a}})
        id_b = res.json()['nodes'][1][0]
        res = requests.post(f"{BASE_URL}/api/operation", json={"operation": "add_node", "params": {"x":20,"y":0,"lane_id":0, "connect_to": id_b}})
        id_c = res.json()['nodes'][2][0]

        # Get Path A->C
        res = requests.post(f"{BASE_URL}/api/operation", json={
            "operation": "get_path",
            "params": {"start_id": id_a, "end_id": id_c}
        })
        self.assertEqual(res.status_code, 200)
        path = res.json()['path_ids']
        self.assertEqual(path, [id_a, id_b, id_c])

    def test_reverse_path(self):
        # Create A->B
        requests.post(f"{BASE_URL}/api/operation", json={"operation": "add_node", "params": {"x":0,"y":0,"lane_id":0}})
        requests.post(f"{BASE_URL}/api/operation", json={"operation": "add_node", "params": {"x":10,"y":0,"lane_id":0, "connect_to": 0}}) # Assuming 0 is checkable

        # Fetch current state to get IDs
        data = requests.get(f"{BASE_URL}/api/data").json()
        id_a = data['nodes'][0][0]
        id_b = data['nodes'][1][0]

        # Reverse A->B
        res = requests.post(f"{BASE_URL}/api/operation", json={
            "operation": "reverse_path",
            "params": {"start_id": id_a, "end_id": id_b}
        })
        self.assertEqual(res.status_code, 200)
        
        # Verify edge is B->A
        edges = res.json()['edges']
        self.assertEqual(edges[0][0], id_b)
        self.assertEqual(edges[0][1], id_a)

    def test_verify_yaw_endpoint(self):
        # Create A->B (Horizontal)
        requests.post(f"{BASE_URL}/api/operation", json={"operation": "add_node", "params": {"x":0,"y":0,"lane_id":0}}) # Yaw 0
        requests.post(f"{BASE_URL}/api/operation", json={"operation": "add_node", "params": {"x":10,"y":0,"lane_id":0, "connect_to": 0}}) 
        
        # Verify Yaw
        res = requests.post(f"{BASE_URL}/api/verify_yaw")
        self.assertEqual(res.status_code, 200)
        results = res.json()['results']
        # Should be aligned (Node A created with 0 yas? No, add_edge updates yaw)
        # DataManager.add_edge updates yaw.
        self.assertEqual(results[0]['status'], 'aligned')

if __name__ == '__main__':
    try:
        # Check if server running
        requests.get(f"{BASE_URL}/api/data")
        unittest.main()
    except requests.exceptions.ConnectionError:
        print("Backend server not running. Please start app.py")
