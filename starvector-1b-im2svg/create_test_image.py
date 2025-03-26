from PIL import Image, ImageDraw

def create_test_image():
    # Create a new image with a white background
    width = 256
    height = 256
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw some simple shapes
    # Circle
    draw.ellipse([50, 50, 150, 150], fill='red')
    
    # Rectangle
    draw.rectangle([100, 100, 200, 200], fill='blue')
    
    # Triangle
    draw.polygon([(50, 200), (100, 100), (150, 200)], fill='green')
    
    # Save the image
    image.save('test_image.png')
    print("Created test_image.png")

if __name__ == "__main__":
    create_test_image() 