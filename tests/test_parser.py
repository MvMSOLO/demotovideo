import unittest
import os
import tempfile
from app.parser import parse_demo_file, create_sample_demo_file

class TestDemoParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cs2_sample_demo_creation_and_parsing(self):
        path = os.path.join(self.temp_dir.name, "sample_cs2.dem")
        create_sample_demo_file(path, game_type="CS2", map_name="de_dust2")

        meta = parse_demo_file(path)
        self.assertTrue(meta["is_valid"])
        self.assertIn("Counter-Strike 2", meta["game"])
        self.assertEqual(meta["map_name"], "de_dust2")
        self.assertEqual(meta["client_name"], "s1mple")
        self.assertGreater(meta["ticks"], 0)
        self.assertEqual(len(meta["highlights"]), 3)

    def test_cs16_sample_demo_creation_and_parsing(self):
        path = os.path.join(self.temp_dir.name, "sample_cs16.dem")
        create_sample_demo_file(path, game_type="CS16", map_name="de_inferno")

        meta = parse_demo_file(path)
        self.assertTrue(meta["is_valid"])
        self.assertIn("GoldSrc", meta["game"])
        self.assertEqual(meta["map_name"], "de_inferno")
        self.assertGreater(meta["ticks"], 0)
        self.assertEqual(len(meta["highlights"]), 3)

    def test_bytes_input(self):
        path = os.path.join(self.temp_dir.name, "sample.dem")
        create_sample_demo_file(path, game_type="CS2", map_name="de_nuke")
        with open(path, "rb") as f:
            b_data = f.read()

        meta = parse_demo_file(b_data)
        self.assertTrue(meta["is_valid"])
        self.assertEqual(meta["map_name"], "de_nuke")

if __name__ == "__main__":
    unittest.main()
