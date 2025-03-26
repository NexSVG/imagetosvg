import numpy as np
from svgpathtools import Path, Arc, CubicBezier, QuadraticBezier
from starvector.data.augmentation import SVGTransforms

def create_test_svg():
    """Create a test SVG with various path types"""
    svg_content = '''
    <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="200" height="200">
        <!-- Simple shapes -->
        <path d="M 50,50 L 150,50 L 150,150 L 50,150 Z" fill="red"/>
        <path d="M 50,50 C 100,0 100,100 150,50" fill="blue"/>
        <path d="M 50,100 Q 100,50 150,100" fill="green"/>
        <path d="M 50,150 A 50,50 0 1,1 150,150" fill="purple"/>
        
        <!-- Complex shape -->
        <path d="M 50,50 C 100,0 100,100 150,50 Q 150,100 100,150 C 50,100 50,0 50,50" fill="orange"/>
    </svg>
    '''
    return svg_content

def test_different_transformations():
    """Test different transformation settings"""
    # Base SVG
    svg_content = create_test_svg()
    
    # Test cases with different transformation settings
    test_cases = [
        {
            'name': 'noise_only',
            'transforms': {
                'noise_std': {'from': 0.1, 'to': 0.3},
                'noise_type': 'perlin',
                'p': 1.0
            }
        },
        {
            'name': 'rotation_only',
            'transforms': {
                'rotate': {'from': -15, 'to': 15},
                'p': 1.0
            }
        },
        {
            'name': 'shift_only',
            'transforms': {
                'shift_re': {'from': -10, 'to': 10},
                'shift_im': {'from': -10, 'to': 10},
                'p': 1.0
            }
        },
        {
            'name': 'scale_only',
            'transforms': {
                'scale': {'from': 0.8, 'to': 1.2},
                'p': 1.0
            }
        },
        {
            'name': 'color_change',
            'transforms': {
                'color_change': True,
                'colors': ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff'],
                'p': 1.0
            }
        },
        {
            'name': 'all_transforms',
            'transforms': {
                'noise_std': {'from': 0.1, 'to': 0.3},
                'noise_type': 'perlin',
                'rotate': {'from': -10, 'to': 10},
                'shift_re': {'from': -5, 'to': 5},
                'shift_im': {'from': -5, 'to': 5},
                'scale': {'from': 0.9, 'to': 1.1},
                'color_change': True,
                'colors': ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff'],
                'p': 0.5
            }
        }
    ]
    
    # Process each test case
    for case in test_cases:
        print(f"\nTesting {case['name']}...")
        
        # Create transformer with current settings
        transformer = SVGTransforms(case['transforms'])
        
        # Apply augmentation
        augmented_svg, _ = transformer.augment(svg_content)
        
        # Save augmented SVG
        output_file = f'augmented_{case["name"]}.svg'
        with open(output_file, 'w') as f:
            f.write(augmented_svg)
        print(f"Saved to {output_file}")

if __name__ == "__main__":
    test_different_transformations() 