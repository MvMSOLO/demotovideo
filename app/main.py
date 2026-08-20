import os
import shutil
import uuid
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.parser import parse_demo_file, create_sample_demo_file
from app.video_engine import generate_base_sample_video
from app.tasks import (
    create_task,
    get_task_status,
    process_demo_to_video_task,
    process_video_to_4k_task,
    process_video_to_smooth_task
)

from app.config import get_base_dir, ensure_dir

BASE_DIR = get_base_dir()
UPLOADS_DIR = ensure_dir(os.path.join(BASE_DIR, "uploads"))
OUTPUTS_DIR = ensure_dir(os.path.join(BASE_DIR, "outputs"))
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

app = FastAPI(
    title="CS Demo & Video Processing Engine",
    description="Convert CS 1.6 & CS2 demos to smooth video, upscale video to 4K, and interpolate video FPS.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.exists(OUTPUTS_DIR):
    app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

@app.get("/")
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Demo to Video API is running."}

@app.post("/api/demo/parse")
async def parse_demo_endpoint(file: UploadFile = File(...)):
    """
    Parses a CS 1.6 or CS2 .dem file and returns detailed header and tick information.
    """
    try:
        content = await file.read()
        metadata = parse_demo_file(content)
        metadata["filename"] = file.filename
        return JSONResponse(content={"status": "success", "metadata": metadata})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse demo file: {str(e)}")

@app.post("/api/demo/convert")
async def convert_demo_endpoint(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    fps: int = Form(60),
    resolution: str = Form("1080p"),
    demo_type: Optional[str] = Form(None)
):
    """
    Accepts uploaded .dem file or generates demo from preset, queuing a background task to convert to smooth video.
    """
    task_id = create_task("demo_to_video")
    upload_dir = ensure_dir(os.path.join(UPLOADS_DIR, task_id))
    file_path = os.path.join(upload_dir, "input.dem")

    if file:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    else:
        # Generate sample demo file based on demo_type or default CS2
        game_kind = "CS16" if (demo_type and "1.6" in demo_type) else "CS2"
        create_sample_demo_file(file_path, game_type=game_kind, map_name="de_dust2")

    background_tasks.add_task(process_demo_to_video_task, task_id, file_path, fps, resolution)

    return {"status": "queued", "task_id": task_id, "message": "Demo video rendering started."}

@app.post("/api/video/to-4k")
async def video_to_4k_endpoint(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    sharpness: float = Form(1.2),
    enhance_colors: bool = Form(True)
):
    """
    Accepts a video upload or creates a sample video, queuing 4K upscaling task.
    """
    task_id = create_task("video_to_4k")
    upload_dir = ensure_dir(os.path.join(UPLOADS_DIR, task_id))
    file_path = os.path.join(upload_dir, "input.mp4")

    if file:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    else:
        generate_base_sample_video(file_path, duration=5, resolution="1280x720", title="4K Upscale Source")

    background_tasks.add_task(process_video_to_4k_task, task_id, file_path, sharpness, enhance_colors)

    return {"status": "queued", "task_id": task_id, "message": "Video to 4K upscaling started."}

@app.post("/api/video/to-smooth")
async def video_to_smooth_endpoint(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    target_fps: int = Form(60),
    smooth_method: str = Form("blend")
):
    """
    Accepts a video upload or sample video, queuing motion smoothing & lag removal task.
    """
    task_id = create_task("video_to_smooth")
    upload_dir = ensure_dir(os.path.join(UPLOADS_DIR, task_id))
    file_path = os.path.join(upload_dir, "input.mp4")

    if file:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    else:
        generate_base_sample_video(file_path, duration=5, resolution="1280x720", title="30 FPS Laggy Source")

    background_tasks.add_task(process_video_to_smooth_task, task_id, file_path, target_fps, smooth_method)

    return {"status": "queued", "task_id": task_id, "message": "Video motion smoothing started."}

@app.get("/api/task/{task_id}")
async def get_task_endpoint(task_id: str):
    task = get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/api/samples/generate-demo")
async def generate_sample_demo_endpoint(game: str = "cs2", map_name: str = "de_dust2"):
    file_id = str(uuid.uuid4())[:8]
    sample_path = os.path.join(OUTPUTS_DIR, f"sample_{game}_{file_id}.dem")
    create_sample_demo_file(sample_path, game_type=game, map_name=map_name)
    return FileResponse(sample_path, filename=f"sample_{game}_{map_name}.dem")
