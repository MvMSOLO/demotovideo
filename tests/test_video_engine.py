import unittest
import os
import tempfile
from app.parser import parse_demo_file, create_sample_demo_file
from app.video_engine import generate_base_sample_video, render_demo_to_video, convert_video_to_4k, convert_video_to_smooth

class TestVideoEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_base_sample_video(self):
        output_path = os.path.join(self.temp_dir.name, "sample.mp4")
        res = generate_base_sample_video(output_path, duration=2, resolution="640x360")
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 1000)

    def test_render_demo_to_video(self):
        demo_path = os.path.join(self.temp_dir.name, "match.dem")
        create_sample_demo_file(demo_path, game_type="CS2", map_name="de_dust2")
        meta = parse_demo_file(demo_path)

        out_video = os.path.join(self.temp_dir.name, "rendered_demo.mp4")
        success = render_demo_to_video(meta, out_video, target_fps=60, resolution="720p")
        self.assertTrue(success)
        self.assertTrue(os.path.exists(out_video))
        self.assertGreater(os.path.getsize(out_video), 1000)

    def test_convert_video_to_4k(self):
        input_path = os.path.join(self.temp_dir.name, "input_low.mp4")
        generate_base_sample_video(input_path, duration=2, resolution="640x360")

        out_4k = os.path.join(self.temp_dir.name, "output_4k.mp4")
        success = convert_video_to_4k(input_path, out_4k, sharpness=1.2)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(out_4k))
        self.assertGreater(os.path.getsize(out_4k), 1000)

    def test_convert_video_to_smooth(self):
        input_path = os.path.join(self.temp_dir.name, "input_laggy.mp4")
        generate_base_sample_video(input_path, duration=2, resolution="640x360")

        out_smooth = os.path.join(self.temp_dir.name, "output_smooth.mp4")
        success = convert_video_to_smooth(input_path, out_smooth, target_fps=60, smooth_method="blend")
        self.assertTrue(success)
        self.assertTrue(os.path.exists(out_smooth))
        self.assertGreater(os.path.getsize(out_smooth), 1000)

if __name__ == "__main__":
    unittest.main()
