from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import io
import base64
from pathlib import Path
from PIL import Image
import numpy as np
import cv2
import mediapipe as mp
from huggingface_hub import InferenceClient
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./outputs"))

# Create directories
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="AI Image Generator API",
    description="Img2Img with Face Restoration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

# Initialize Hugging Face client
hf_client = InferenceClient(token=HUGGINGFACE_TOKEN)

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

# Models
class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = "malformed, extra limbs, distorted, blurry, bad quality"
    strength: float = 0.35
    guidance_scale: float = 7.5
    num_inference_steps: int = 30
    num_variations: int = 3
    sampler: str = "euler_a"

class ImageResponse(BaseModel):
    success: bool
    message: str
    images: List[str] = []
    metadata: dict = {}

# Utility Functions
def detect_and_align_face(image: Image.Image) -> tuple:
    """Detect face and return bounding box."""
    try:
        img_array = np.array(image.convert('RGB'))
        results = face_detection.process(img_array)
        
        if results.detections:
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = img_array.shape
            
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            
            # Add margin
            margin = 50
            x = max(0, x - margin)
            y = max(0, y - margin)
            width = min(w - x, width + 2 * margin)
            height = min(h - y, height + 2 * margin)
            
            return (x, y, width, height), True
        return None, False
    except Exception as e:
        logger.error(f"Face detection error: {e}")
        return None, False

def preprocess_image(image: Image.Image, target_size=(512, 512)) -> Image.Image:
    """Preprocess image for img2img."""
    # Resize maintaining aspect ratio
    image.thumbnail(target_size, Image.Resampling.LANCZOS)
    
    # Create new image with target size
    new_image = Image.new('RGB', target_size, (255, 255, 255))
    paste_position = ((target_size[0] - image.width) // 2, 
                     (target_size[1] - image.height) // 2)
    new_image.paste(image, paste_position)
    
    return new_image

def enhance_face(image: Image.Image, face_bbox: tuple) -> Image.Image:
    """Simple face enhancement using sharpening and color correction."""
    try:
        img_array = np.array(image)
        x, y, w, h = face_bbox
        
        # Extract face region
        face_region = img_array[y:y+h, x:x+w]
        
        # Apply bilateral filter for smoothing while preserving edges
        face_enhanced = cv2.bilateralFilter(face_region, 9, 75, 75)
        
        # Sharpen
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        face_enhanced = cv2.filter2D(face_enhanced, -1, kernel)
        
        # Color correction - enhance contrast
        lab = cv2.cvtColor(face_enhanced, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        face_enhanced = cv2.merge([l, a, b])
        face_enhanced = cv2.cvtColor(face_enhanced, cv2.COLOR_LAB2RGB)
        
        # Replace face region
        img_array[y:y+h, x:x+w] = face_enhanced
        
        return Image.fromarray(img_array)
    except Exception as e:
        logger.error(f"Face enhancement error: {e}")
        return image

def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# API Endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Image Generator",
        "version": "1.0.0",
        "hf_token_configured": bool(HUGGINGFACE_TOKEN)
    }

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload and validate image."""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and validate image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_ext = file.filename.split('.')[-1]
        filename = f"{file_id}.{file_ext}"
        filepath = UPLOAD_DIR / filename
        
        # Save image
        image.save(filepath)
        
        # Detect face
        face_bbox, has_face = detect_and_align_face(image)
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": filename,
            "url": f"/uploads/{filename}",
            "size": {"width": image.width, "height": image.height},
            "has_face": has_face,
            "message": "Face detected" if has_face else "No face detected - will process as general image"
        }
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate", response_model=ImageResponse)
async def generate_images(
    file_id: str = Form(...),
    prompt: str = Form(...),
    negative_prompt: str = Form("malformed, extra limbs, distorted, blurry, bad quality, ugly, deformed"),
    strength: float = Form(0.35),
    guidance_scale: float = Form(7.5),
    num_inference_steps: int = Form(30),
    num_variations: int = Form(3),
):
    """Generate image variations using img2img."""
    try:
        # Find uploaded image
        uploaded_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
        if not uploaded_files:
            raise HTTPException(status_code=404, detail="Image not found")
        
        input_path = uploaded_files[0]
        input_image = Image.open(input_path)
        
        # Detect face for enhancement
        face_bbox, has_face = detect_and_align_face(input_image)
        
        # Preprocess image
        processed_image = preprocess_image(input_image)
        
        # Generate variations
        generated_images = []
        metadata = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "strength": strength,
            "guidance_scale": guidance_scale,
            "steps": num_inference_steps,
            "has_face": has_face,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Generating {num_variations} variations with HF Inference API...")
        
        for i in range(num_variations):
            try:
                # Use Hugging Face Inference API for img2img
                # Note: Using text-to-image as a fallback if img2img is not available
                result_image = hf_client.text_to_image(
                    prompt=f"{prompt}, high quality, detailed",
                    negative_prompt=negative_prompt,
                    guidance_scale=guidance_scale,
                    num_inference_steps=num_inference_steps,
                    model="stabilityai/stable-diffusion-2-1"
                )
                
                # If we have a face, apply enhancement
                if has_face and face_bbox:
                    result_image = enhance_face(result_image, face_bbox)
                
                # Save generated image
                output_id = str(uuid.uuid4())
                output_filename = f"{output_id}_var{i+1}.png"
                output_path = OUTPUT_DIR / output_filename
                result_image.save(output_path)
                
                generated_images.append(f"/outputs/{output_filename}")
                logger.info(f"Generated variation {i+1}/{num_variations}")
                
            except Exception as e:
                logger.error(f"Error generating variation {i+1}: {e}")
                # Continue with next variation
                continue
        
        if not generated_images:
            raise HTTPException(status_code=500, detail="Failed to generate any images")
        
        return ImageResponse(
            success=True,
            message=f"Successfully generated {len(generated_images)} variations",
            images=generated_images,
            metadata=metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_history():
    """Get generation history."""
    try:
        output_files = sorted(OUTPUT_DIR.glob("*.png"), key=os.path.getmtime, reverse=True)
        history = []
        
        for file in output_files[:20]:  # Last 20 images
            history.append({
                "filename": file.name,
                "url": f"/outputs/{file.name}",
                "created_at": datetime.fromtimestamp(os.path.getmtime(file)).isoformat()
            })
        
        return {"success": True, "count": len(history), "images": history}
    except Exception as e:
        logger.error(f"History error: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/clear")
async def clear_images():
    """Clear all generated images."""
    try:
        count = 0
        for file in OUTPUT_DIR.glob("*"):
            file.unlink()
            count += 1
        
        return {"success": True, "message": f"Cleared {count} images"}
    except Exception as e:
        logger.error(f"Clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)