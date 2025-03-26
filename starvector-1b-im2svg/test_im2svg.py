import torch
from PIL import Image
import matplotlib.pyplot as plt
from starvector.model.starvector_arch import StarVectorForCausalLM
from starvector.data.util import process_and_rasterize_svg
from transformers import AutoConfig
import os

def test_im2svg(image_path):
    # Check CUDA availability
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"Available GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # Disable flash attention and set environment variables
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
    os.environ["ATTENTION_IMPLEMENTATION"] = "eager"
    
    # Load the model
    model_name = "starvector/starvector-1b-im2svg"
    config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
    config.attn_implementation = "eager"
    config.use_flash_attention_2 = False
    
    starvector = StarVectorForCausalLM.from_pretrained(
        model_name, 
        config=config,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_flash_attention_2=False,
        attn_implementation="eager",
        trust_remote_code=True
    )
    
    # Move model to appropriate device
    starvector = starvector.to(device)
    starvector.eval()
    
    # Load and process the image
    image_pil = Image.open(image_path)
    image_pil = image_pil.convert('RGB')
    
    # Process image for the model
    image = starvector.process_images([image_pil])[0].to(torch.float16 if device == "cuda" else torch.float32)
    if device == "cuda":
        image = image.cuda()
    batch = {"image": image}
    
    # Generate SVG
    print("Generating SVG...")
    with torch.no_grad():
        svg_output = starvector.generate_im2svg(
            batch,
            max_length=4000,
            temperature=1.5,
            length_penalty=-1,
            repetition_penalty=3.1
        )[0]
    
    # Process the generated SVG and create visualization
    svg, raster_image = process_and_rasterize_svg(svg_output)
    
    # Save the SVG output
    with open('output.svg', 'w') as f:
        f.write(svg)
    print("SVG saved to output.svg")
    
    # Display and save comparison
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.imshow(image_pil)
    plt.title('Original Image')
    plt.axis('off')
    
    plt.subplot(1, 2, 2)
    plt.imshow(raster_image)
    plt.title('Generated SVG')
    plt.axis('off')
    
    plt.savefig('comparison.png')
    plt.close()
    print("Comparison saved to comparison.png")

if __name__ == "__main__":
    image_path = "test_image.png"
    test_im2svg(image_path) 