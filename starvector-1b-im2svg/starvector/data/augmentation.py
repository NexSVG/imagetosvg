import numpy as np
from svgpathtools import (
    Path, Arc, CubicBezier, QuadraticBezier,
    parse_path)
import os 
from opensimplex import OpenSimplex
import random
import re
from bs4 import BeautifulSoup
from starvector.data.util import get_viewbox_size, clean_attributes, paths2str

class SVGTransforms:
    def __init__(self, transforms):
        self.transforms = transforms
        self.noise_gen = OpenSimplex(seed=np.random.randint(0, 1000000))
        self.noise_std = self.transforms.get('noise_std', False) 
        self.noise_type = self.transforms.get('noise_type', False)
        self.rotate = self.transforms.get('rotate', False)
        self.shift_re = self.transforms.get('shift_re', False)
        self.shift_im = self.transforms.get('shift_im', False)
        self.scale = self.transforms.get('scale', False)
        self.color_noise = self.transforms.get('color_noise', False)
        self.p = self.transforms.get('p', 0.5)
        self.color_change = self.transforms.get('color_change', False)
        self.colors = self.transforms.get('colors', ['#ff0000', '#0000ff', '#000000'])

    def sample_transformations(self):
        """Sample random values for transformations"""
        if self.rotate:
            self.rotation_angle = np.random.uniform(self.rotate['from'], self.rotate['to'])
        if self.shift_re:
            self.shift_re_value = np.random.uniform(self.shift_re['from'], self.shift_re['to'])
        if self.shift_im:
            self.shift_im_value = np.random.uniform(self.shift_im['from'], self.shift_im['to'])
        if self.scale:
            self.scale_value = np.random.uniform(self.scale['from'], self.scale['to'])
        if self.color_noise:
            self.color_noise_std = np.random.uniform(self.color_noise['from'], self.color_noise['to'])

    def add_noise(self, path, noise_std):
        """Add Perlin noise to SVG path coordinates"""
        if random.random() > self.p:
            return path
            
        # Get path segments
        segments = path._segments
        
        # Create new segments with noise
        new_segments = []
        for segment in segments:
            # Get control points
            points = segment.bpoints()
            
            # Add noise to each point
            noisy_points = []
            for i, point in enumerate(points):
                # Generate noise with different offsets for x and y
                x_noise = self.noise_gen.noise2(i * 20, 0) * noise_std
                y_noise = self.noise_gen.noise2(0, i * 20) * noise_std
                
                # Apply noise to coordinates
                noisy_point = complex(
                    point.real + x_noise,
                    point.imag + y_noise
                )
                noisy_points.append(noisy_point)
            
            # Create new segment with noisy points
            if isinstance(segment, CubicBezier):
                new_segment = CubicBezier(*noisy_points)
            elif isinstance(segment, QuadraticBezier):
                new_segment = QuadraticBezier(*noisy_points)
            elif isinstance(segment, Arc):
                new_segment = Arc(
                    noisy_points[0],
                    noisy_points[1],
                    segment.radius,
                    segment.rotation,
                    segment.large_arc,
                    segment.sweep
                )
            else:
                new_segment = segment
                
            new_segments.append(new_segment)
        
        # Create new path with noisy segments
        return Path(*new_segments)
    
    def do_rotate(self, path, viewbox_width, viewbox_height):
        """Apply rotation to path"""
        if not self.rotate or random.random() > self.p:
            return path
            
        # Get center point
        center = complex(viewbox_width/2, viewbox_height/2)
        
        # Rotate path around center
        return path.rotated(self.rotation_angle, center)
    
    def do_shift(self, path):
        """Apply shift to path"""
        if not (self.shift_re or self.shift_im) or random.random() > self.p:
            return path
            
        shift = complex(
            self.shift_re_value if self.shift_re else 0,
            self.shift_im_value if self.shift_im else 0
        )
        
        return path.translated(shift)
    
    def do_scale(self, path):
        """Apply scaling to path"""
        if not self.scale or random.random() > self.p:
            return path
            
        return path.scaled(self.scale_value)
    
    def do_color_change(self, attributes):
        """Apply color change to path attributes"""
        if not self.color_change or random.random() > self.p:
            return attributes
            
        if 'fill' in attributes:
            attributes['fill'] = random.choice(self.colors)
        if 'stroke' in attributes:
            attributes['stroke'] = random.choice(self.colors)
            
        return attributes
    
    def augment(self, svg_content):
        """Apply transformations to SVG content"""
        if os.path.isfile(svg_content):
            with open(svg_content, 'r') as f:
                svg_content = f.read()
        
        # Sample transformations
        self.sample_transformations()
        
        # Parse SVG content
        soup = BeautifulSoup(svg_content, 'xml')
        svg_tag = soup.find('svg')
        if not svg_tag:
            return svg_content, None
        
        # Get viewbox size
        viewbox_width, viewbox_height = get_viewbox_size(svg_content)
        
        # Process all path elements
        paths_and_attributes = []
        for path_tag in soup.find_all('path'):
            path_data = path_tag.get('d', '')
            if path_data:
                try:
                    path = parse_path(path_data)
                    attributes = dict(path_tag.attrs)
                    
                    # Apply transformations
                    path = self.do_rotate(path, viewbox_width, viewbox_height)
                    path = self.do_shift(path)
                    path = self.do_scale(path)
                    
                    if self.noise_std:
                        noise_std = random.uniform(
                            self.noise_std['from'],
                            self.noise_std['to']
                        )
                        path = self.add_noise(path, noise_std)
                    
                    # Apply color change
                    attributes = self.do_color_change(attributes)
                    
                    paths_and_attributes.append((path, attributes))
                except Exception as e:
                    print(f"Error processing path: {e}")
                    continue
        
        # Create new SVG content
        svg_attrs = ' '.join([f'{k}="{v}"' for k, v in svg_tag.attrs.items()])
        augmented_svg = f'<svg {svg_attrs}>'
        
        # Add paths
        for path, attributes in paths_and_attributes:
            path_attrs = ' '.join([f'{k}="{v}"' for k, v in attributes.items()])
            augmented_svg += f'<path d="{path.d()}" {path_attrs}/>'
        
        augmented_svg += '</svg>'
        
        return augmented_svg, None  # Return None for image since we're not rendering
