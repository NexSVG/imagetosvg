from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import io
import os
import torch
import traceback
from starvector import StarVectorForCausalLM, process_images
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/", StaticFiles(directory="../nexsvg-frontend", html=True), name="static")

@app.post("/convert")
async def convert_to_svg(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file: {file.filename}")
        
        # Read the uploaded image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = image.convert('RGB')
        logger.info(f"Image loaded and converted to RGB: {image.size}")

        try:
            # For testing, return a simple SVG
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
            <svg width="{image.width}" height="{image.height}" version="1.1" xmlns="http://www.w3.org/2000/svg">
                <rect width="{image.width}" height="{image.height}" fill="#ffffff"/>
                <circle cx="{image.width/2}" cy="{image.height/2}" r="{min(image.width, image.height)/4}" fill="#0ea5e9"/>
            </svg>'''
            
            logger.info("Generated test SVG successfully")
            return Response(content=svg_content, media_type="image/svg+xml")
            
        except Exception as model_error:
            logger.error(f"Error in model processing: {str(model_error)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Model processing failed", "detail": str(model_error)}
            )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Request processing failed", "detail": str(e)}
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# For testing purposes
@app.get("/")
async def root():
    return {"message": "SVG Conversion API is running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 