import numpy as np
from svgpathtools import Path, Arc, CubicBezier, QuadraticBezier
from starvector.data.augmentation import SVGTransforms

def create_test_svg():
    # Create a simple SVG with different path types
    svg_content = '''
    <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="200" height="200">
        <!-- Cubic Bezier curve -->
        <path d="M 50,50 C 100,0 100,100 150,50" fill="red"/>
        
        <!-- Quadratic Bezier curve -->
        <path d="M 50,100 Q 100,50 150,100" fill="blue"/>
        
        <!-- Arc -->
        <path d="M 50,150 A 50,50 0 1,1 150,150" fill="green"/>
    </svg>
    '''
    return svg_content

def test_augmentation():
    # Create test SVG
    svg_content = create_test_svg()
    
    # Define transformations with different noise settings
    transformations = {
        'noise_std': {'from': 0.1, 'to': 0.3},
        'noise_type': 'perlin',
        'rotate': {'from': -10, 'to': 10},
        'shift_re': {'from': -5, 'to': 5},
        'shift_im': {'from': -5, 'to': 5},
        'scale': {'from': 0.9, 'to': 1.1},
        'color_noise': {'from': 0.1, 'to': 0.2},
        'p': 0.5
    }
    
    # Create SVGTransforms instance
    transformer = SVGTransforms(transformations)
    
    # Apply augmentation
    augmented_svg, _ = transformer.augment(svg_content)
    
    # Print original and augmented SVGs
    print("Original SVG:")
    print(svg_content)
    print("\nAugmented SVG:")
    print(augmented_svg)
    
    # Save augmented SVG to file
    with open('augmented_test.svg', 'w') as f:
        f.write(augmented_svg)
    print("\nAugmented SVG saved to 'augmented_test.svg'")

if __name__ == "__main__":
    test_augmentation() 