from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import shutil
import os
import uuid
import zipfile
import tempfile
from datetime import datetime

# Import feature modules
from features.face_cluster import cluster_by_face
from features.remove_duplicates import remove_duplicates
from features.remove_blur import remove_blur_images
from features.remove_bad_angles import remove_bad_angles
from features.sort_by_date import sort_by_date
from features.remove_background import remove_background

app = FastAPI(title="Image Cluster API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temporary directories for uploads and processed images
UPLOAD_DIR = "temp/uploads"
PROCESSED_DIR = "temp/processed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@app.post("/api/upload")
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload multiple images to the server"""
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    file_paths = []
    for file in files:
        if not file.content_type.startswith('image/'):
            continue
        
        file_path = os.path.join(session_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(file_path)
    
    return {"session_id": session_id, "file_count": len(file_paths)}

@app.post("/api/process")
async def process_images(
    session_id: str = Form(...),
    cluster_face: Optional[bool] = Form(False),
    remove_duplicates_flag: Optional[bool] = Form(False),
    remove_blur: Optional[bool] = Form(False),
    remove_bad_angles_flag: Optional[bool] = Form(False),
    sort_date: Optional[bool] = Form(False),
    remove_background_flag: Optional[bool] = Form(False),
    face_sample: Optional[UploadFile] = File(None)
):
    """Process images with selected features"""
    # Validate session
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create output directory for this session
    output_dir = os.path.join(PROCESSED_DIR, session_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy all files to output directory as starting point
    for filename in os.listdir(session_dir):
        src_path = os.path.join(session_dir, filename)
        dst_path = os.path.join(output_dir, filename)
        shutil.copy2(src_path, dst_path)
    
    # Process with selected features
    image_paths = [os.path.join(output_dir, f) for f in os.listdir(output_dir)]
    
    # Apply face clustering if selected
    if cluster_face:
        face_sample_path = None
        if face_sample:
            # Save the face sample image
            face_sample_path = os.path.join(output_dir, "face_sample.jpg")
            with open(face_sample_path, "wb") as buffer:
                shutil.copyfileobj(face_sample.file, buffer)
        
        image_paths = cluster_by_face(image_paths, output_dir, face_sample_path)
    
    # Apply duplicate removal if selected
    if remove_duplicates_flag:
        image_paths = remove_duplicates(image_paths, output_dir)
    
    # Apply blur removal if selected
    if remove_blur:
        image_paths = remove_blur_images(image_paths, output_dir)
    
    # Apply bad angle removal if selected
    if remove_bad_angles_flag:
        image_paths = remove_bad_angles(image_paths, output_dir)
    
    # Apply date sorting if selected
    if sort_date:
        image_paths = sort_by_date(image_paths, output_dir)
    
    # Apply background removal if selected
    if remove_background_flag:
        image_paths = remove_background(image_paths, output_dir)
    
    # Create a list of processed images with metadata
    processed_images = []
    for path in image_paths:
        if os.path.exists(path):
            filename = os.path.basename(path)
            stat = os.stat(path)
            processed_images.append({
                "filename": filename,
                "path": path,
                "size": stat.st_size,
                "date": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return {"session_id": session_id, "processed_images": processed_images}

@app.get("/api/download/{session_id}")
async def download_results(session_id: str):
    """Download processed images as a ZIP file"""
    # Validate session
    output_dir = os.path.join(PROCESSED_DIR, session_id)
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create a temporary ZIP file
    zip_filename = f"processed_images_{session_id}.zip"
    zip_path = os.path.join(tempfile.gettempdir(), zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)
    
    return FileResponse(
        path=zip_path,
        filename=zip_filename,
        media_type="application/zip"
    )

@app.on_event("startup")
def startup_event():
    """Clean up temporary directories on startup"""
    for dir_path in [UPLOAD_DIR, PROCESSED_DIR]:
        if os.path.exists(dir_path):
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)

# Mount static files (for serving the frontend) - moved after API routes
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)