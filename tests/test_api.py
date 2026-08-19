import unittest
import os
import time
from fastapi.testclient import TestClient
from app.main import app

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        res = self.client.get("/")
        self.assertIn(res.status_code, [200, 404]) # 404 if index.html isn't created yet or 200 if server responds

    def test_sample_demo_generation(self):
        res = self.client.get("/api/samples/generate-demo?game=cs2&map_name=de_dust2")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(res.content), 100)

    def test_demo_convert_flow(self):
        # Trigger conversion without file (uses synthetic sample)
        res = self.client.post("/api/demo/convert", data={"fps": 60, "resolution": "720p"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "queued")
        task_id = data["task_id"]

        # Poll task until completion
        completed = False
        for _ in range(15):
            t_res = self.client.get(f"/api/task/{task_id}")
            self.assertEqual(t_res.status_code, 200)
            t_data = t_res.json()
            if t_data["status"] == "completed":
                completed = True
                self.assertIn("video_url", t_data["result"])
                break
            time.sleep(0.5)

        self.assertTrue(completed)

    def test_video_to_4k_flow(self):
        res = self.client.post("/api/video/to-4k", data={"sharpness": 1.2, "enhance_colors": True})
        self.assertEqual(res.status_code, 200)
        task_id = res.json()["task_id"]

        completed = False
        for _ in range(15):
            t_res = self.client.get(f"/api/task/{task_id}")
            t_data = t_res.json()
            if t_data["status"] == "completed":
                completed = True
                self.assertIn("video_url", t_data["result"])
                break
            time.sleep(0.5)

        self.assertTrue(completed)

    def test_video_to_smooth_flow(self):
        res = self.client.post("/api/video/to-smooth", data={"target_fps": 60, "smooth_method": "blend"})
        self.assertEqual(res.status_code, 200)
        task_id = res.json()["task_id"]

        completed = False
        for _ in range(15):
            t_res = self.client.get(f"/api/task/{task_id}")
            t_data = t_res.json()
            if t_data["status"] == "completed":
                completed = True
                self.assertIn("video_url", t_data["result"])
                break
            time.sleep(0.5)

        self.assertTrue(completed)

if __name__ == "__main__":
    unittest.main()
