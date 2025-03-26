from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from PIL import Image
import io
import os
import torch
import logging
from starvector import StarVectorForCausalLM, process_images

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NexSVG API",
    description="Convert images to SVG using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/convert", 
         description="Convert an image to SVG format",
         responses={
             200: {"content": {"image/svg+xml": {}}},
             400: {"description": "Invalid input"},
             500: {"description": "Server error"}
         })
async def convert_to_svg(file: UploadFile = File(...)):
    try:
        logger.info(f"Processing file: {file.filename}")
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = image.convert('RGB')
        logger.info(f"Image loaded and converted to RGB: {image.size}")

        try:
            # Process the image using StarVector
            processed_image = process_images([image])[0].to(torch.float16).cuda()
            
            # Load the model
            model = StarVectorForCausalLM.from_pretrained("starvector/starvector-1b-im2svg").cuda()
            model.eval()

            # Generate SVG
            with torch.no_grad():
                svg_output = model.generate_im2svg(
                    processed_image,
                    max_length=4000,
                    temperature=1.5,
                    length_penalty=-1,
                    repetition_penalty=3.1
                )
            
            logger.info("Successfully generated SVG")
            return Response(content=svg_output, media_type="image/svg+xml")
            
        except Exception as model_error:
            logger.error(f"Model error: {str(model_error)}")
            return JSONResponse(
                status_code=500,
                content={"error": "SVG generation failed", "detail": str(model_error)}
            )

    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Request processing failed", "detail": str(e)}
        )

@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 