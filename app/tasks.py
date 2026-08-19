import uuid
import asyncio
import os
import time
import logging
from typing import Dict, Any, Optional
from app.parser import parse_demo_file, create_sample_demo_file
from app.video_engine import (
    render_demo_to_video,
    convert_video_to_4k,
    convert_video_to_smooth,
    generate_base_sample_video
)

logger = logging.getLogger(__name__)

# In-memory store for task states
# Schema: task_id -> { id, type, status, progress, result, error, created_at }
tasks_db: Dict[str, Dict[str, Any]] = {}

def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    return tasks_db.get(task_id)

def create_task(task_type: str) -> str:
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {
        "id": task_id,
        "type": task_type,
        "status": "queued",
        "progress": 0,
        "result": None,
        "error": None,
        "created_at": time.time()
    }
    return task_id

async def process_demo_to_video_task(task_id: str, file_path: str, fps: int, resolution: str):
    task = tasks_db.get(task_id)
    if not task:
        return

    try:
        task["status"] = "processing"
        task["progress"] = 15
        await asyncio.sleep(0.5)

        # 1. Parse demo
        meta = parse_demo_file(file_path)
        task["progress"] = 35
        task["metadata"] = meta
        await asyncio.sleep(0.5)

        # 2. Render smooth video
        output_dir = os.path.join("outputs", task_id)
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "rendered_demo.mp4")

        task["progress"] = 60
        success = await asyncio.to_thread(render_demo_to_video, meta, out_path, fps, resolution)

        if success and os.path.exists(out_path):
            task["progress"] = 100
            task["status"] = "completed"
            task["result"] = {
                "video_url": f"/outputs/{task_id}/rendered_demo.mp4",
                "metadata": meta,
                "fps": fps,
                "resolution": resolution
            }
        else:
            task["status"] = "failed"
            task["error"] = "FFmpeg demo rendering failed."
    except Exception as e:
        logger.exception("Task execution error")
        task["status"] = "failed"
        task["error"] = str(e)


async def process_video_to_4k_task(task_id: str, input_path: str, sharpness: float, enhance_colors: bool):
    task = tasks_db.get(task_id)
    if not task:
        return

    try:
        task["status"] = "processing"
        task["progress"] = 20
        await asyncio.sleep(0.5)

        output_dir = os.path.join("outputs", task_id)
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "video_4k.mp4")

        task["progress"] = 50
        success = await asyncio.to_thread(convert_video_to_4k, input_path, out_path, sharpness, enhance_colors)

        if success and os.path.exists(out_path):
            task["progress"] = 100
            task["status"] = "completed"
            task["result"] = {
                "video_url": f"/outputs/{task_id}/video_4k.mp4",
                "resolution": "3840x2160 (4K Ultra-HD)",
                "sharpness": sharpness,
                "enhance_colors": enhance_colors
            }
        else:
            task["status"] = "failed"
            task["error"] = "FFmpeg 4K upscaling failed."
    except Exception as e:
        logger.exception("Task execution error")
        task["status"] = "failed"
        task["error"] = str(e)


async def process_video_to_smooth_task(task_id: str, input_path: str, target_fps: int, smooth_method: str):
    task = tasks_db.get(task_id)
    if not task:
        return

    try:
        task["status"] = "processing"
        task["progress"] = 25
        await asyncio.sleep(0.5)

        output_dir = os.path.join("outputs", task_id)
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "video_smooth.mp4")

        task["progress"] = 65
        success = await asyncio.to_thread(convert_video_to_smooth, input_path, out_path, target_fps, smooth_method)

        if success and os.path.exists(out_path):
            task["progress"] = 100
            task["status"] = "completed"
            task["result"] = {
                "video_url": f"/outputs/{task_id}/video_smooth.mp4",
                "target_fps": target_fps,
                "method": smooth_method,
                "lag_reduced": True
            }
        else:
            task["status"] = "failed"
            task["error"] = "FFmpeg motion smoothing failed."
    except Exception as e:
        logger.exception("Task execution error")
        task["status"] = "failed"
        task["error"] = str(e)
