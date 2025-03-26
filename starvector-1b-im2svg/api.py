from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import torch
from starvector.model.starvector_arch import StarVectorForCausalLM
from transformers import AutoConfig
import os
import base64
from io import BytesIO

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model variable
model = None

def load_model():
    global model
    if model is None:
        print("Loading model...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        
        model_name = "starvector/starvector-1b-im2svg"
        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        config.attn_implementation = "eager"
        config.use_flash_attention_2 = False
        
        model = StarVectorForCausalLM.from_pretrained(
            model_name, 
            config=config,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            use_flash_attention_2=False,
            attn_implementation="eager",
            trust_remote_code=True
        )
        
        model = model.to(device)
        model.eval()
        print("Model loaded successfully!")

@app.on_event("startup")
async def startup_event():
    load_model()

@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    try:
        # Read the uploaded image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = image.convert('RGB')
        
        # Process image for the model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        processed_image = model.process_images([image])[0].to(torch.float16 if device == "cuda" else torch.float32)
        if device == "cuda":
            processed_image = processed_image.cuda()
        
        # Generate SVG
        with torch.no_grad():
            svg_output = model.generate_im2svg(
                {"image": processed_image},
                max_length=4000,
                temperature=1.5,
                length_penalty=-1,
                repetition_penalty=3.1
            )[0]
        
        return {"svg": svg_output}
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None} 